#!/usr/bin/env python
'''Monitor temperature.

Adding a new sensor
===================

1. Mirror all data. The steps below will delete the values in the
   existing rrd database.

2. Add columns for the new sensor to the relevant tables in the sqlite
   database. For example::

      for x in `sqlite3 csvdb ".tables" | xargs --max-args=1 | grep top_temperature`; do  \
           sqlite3 csvdb "ALTER TABLE $x ADD COLUMN BoilerWater FLOAT;"; done

3. Stop the monitoring daemon

3. Delete old rrd database. For example::

      rm /mnt/ramdisk/temperature.rrd

4. Restart the monitoring daemon. The new rrd will be
   automatically created.

'''

import os
import time
import logging
import rrdtool
import subprocess
import socket

# third party libs
from daemon import runner

HOSTNAME = socket.gethostname()

CONFIG = {
    "KeevaRoomBack": '10-0008029db5bc',
    "KeevaRoomTop": 'o28.3DA0D4040000',
    "KeevaCupBoard": '10-0008029d938d',
    "AiringCabinet": '10-0008029db6c3',
    "Attic": '10-0008029da542',
    "NiamhRoomBack": "o28.6BFED3040000",
    "NiamhRoomTop": "o28.45C0D4040000",
    "LivingRoomWindow": "28-000004d41fb1",
    "LivingRoomCupBoard": "28-000004d45cae",
    "LandingTop": "o10.ED859D020800",
    "LandingMiddle": "28-000004d3f73e",
    "LandingBottom": "10-0008029dc359",
    "HotWater": "o10.B1B29D020800",
    "BoilerWater": "o10.0ec89d020800",
    "HallwayTop": "28-000004d49218",
    "BackRoomFront": "28-000004d422f5",
    "HallwayBottom": "28-00000584f21d",
    "BackRoomBack": "28-0000058528bc",

}

SENSOR_GROUPS = [
    ("KeevaRoomBack",
     "KeevaRoomTop",
     "KeevaCupBoard",
     "AiringCabinet",
     "Attic",
     "NiamhRoomBack",
     "NiamhRoomTop",
     "LandingTop",
     "HotWater",
     "BoilerWater"),
    ("LivingRoomWindow",
     "LivingRoomCupBoard",
     "LandingMiddle",
     "LandingBottom"),
    ("HallwayTop",
     "HallwayBottom",
     "BackRoomBack",
     "BackRoomFront"),
]

MIN_TEMPERATURE = -50
MAX_TEMPERATURE = 100

CACHE = {}

# set heart-beat
HEART_BEAT = 10

CARBON_SERVER = '192.168.0.51'
CARBON_PORT = 2003

# aggregates
SHORT_TERM_DAYS = 7
MEDIUM_TERM_DAYS = 30
LONG_TERM_DAYS = 90

# number of readings and periods in days for profiles
SHORT_TERM_VALUES_PER_AGGREGATE = 1
SHORT_TERM_NUM_VALUES = SHORT_TERM_DAYS * \
    24 * 60 // SHORT_TERM_VALUES_PER_AGGREGATE
MEDIUM_TERM_VALUES_PER_AGGREGATE = 5
MEDIUM_TERM_NUM_VALUES = MEDIUM_TERM_DAYS * \
    24 * 60 // MEDIUM_TERM_VALUES_PER_AGGREGATE
LONG_TERM_VALUES_PER_AGGREGATE = 10
LONG_TERM_NUM_VALUES = LONG_TERM_DAYS * \
    24 * 60 // LONG_TERM_VALUES_PER_AGGREGATE

##########################################################################
##########################################################################
##########################################################################
##########################################################################
# Daemon part
##########################################################################


class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        # tty not available for a spice
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = '/mnt/ramdisk/temperature_daemon.pid'
        self.pidfile_timeout = 5

        # open tcp connection
        self.connection = None

        if HOSTNAME == "top-pi":
            self.sensor_group = 0
        elif HOSTNAME == "mid-pi":
            self.sensor_group = 1
        elif HOSTNAME == "bottom-pi":
            self.sensor_group = 2
        else:
            raise ValueError('unknown host')
            
    def run(self):
        '''main loop. 
        '''

        self.createDatabase()

        while True:
            values = []
            success = {}
            for key in SENSOR_GROUPS[self.sensor_group]:
                logger.debug("acquiring %s" % key)
                fn = CONFIG[key]

                if fn[0] == "o":
                    try:
                        temperature = subprocess.check_output(
                            ["owread", "/%s/temperature" % fn[1:]])
                        success[key] = 'ok'
                    except subprocess.CalledProcessError:
                        logger.debug("%s from cache" % key)
                        temperature = CACHE.get(key, 0)
                        success[key] = 'fail'
                    temperature = float(temperature)
                else:
                    try:
                        tfile = open(
                            "/sys/bus/w1/devices/w1_bus_master1/%s/w1_slave" % fn)
                    except IOError:
                        tfile = None
                    if tfile:
                        text = tfile.readlines()
                        tfile.close()
                        status, temperature_data = text
                        if not status.endswith("YES\n"):
                            logger.debug("%s from cache" % key)
                            temperature = CACHE.get(key, 0)
                        else:
                            temperature_data = temperature_data.split()[-1]
                            temperature = float(temperature_data[2:])
                            temperature = temperature / 1000
                        success[key] = 'ok'
                    else:
                        logger.debug("%s from cache" % key)
                        success[key] = 'fail'
                        temperature = CACHE.get(key, 0)

                CACHE[key] = temperature

                values.append(temperature)

            logger.info("acquired values: %s" % str(values))
            self.updateDatabase(values)
            logger.info("status: %s" %
                        (",".join(
                            ['%s=%s' % (x, y) for x, y in success.items()])))
            time.sleep(HEART_BEAT)

    def updateDatabase(self, values):
        '''send data to carbon server'''
        

    def createDatabase(self):
        '''create rrd databases. Existing databases will not be overwritten'''

        params = globals()
        params.update(locals())

        if not os.path.exists(self.rrd_temperature):
            logger.info("creating new rrd database %s" % self.rrd_temperature)
            data_sources = []
            for key in SENSOR_GROUPS[self.sensor_group]:
                mi, ma = MIN_TEMPERATURE, MAX_TEMPERATURE
                data_sources.append('DS:%s:GAUGE:%i:%i:%i' % (key, 2 * HEART_BEAT,
                                                              mi, ma))

            rra = [
                # short-term
                'RRA:AVERAGE:0.5:%(SHORT_TERM_VALUES_PER_AGGREGATE)i:%(SHORT_TERM_NUM_VALUES)i',
                # medium term
                'RRA:AVERAGE:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                'RRA:MIN:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                'RRA:MAX:0.5:%(MEDIUM_TERM_VALUES_PER_AGGREGATE)i:%(MEDIUM_TERM_NUM_VALUES)i',
                # longterm profile
                'RRA:AVERAGE:0.5:%(LONG_TERM_VALUES_PER_AGGREGATE)i:%(LONG_TERM_NUM_VALUES)i',
                'RRA:MIN:0.5:%(LONG_TERM_VALUES_PER_AGGREGATE)i:%(LONG_TERM_NUM_VALUES)i',
                'RRA:MAX:0.5:%(LONG_TERM_VALUES_PER_AGGREGATE)i:%(LONG_TERM_NUM_VALUES)i',
            ]

            rra = [x % params for x in rra]

            rrdtool.create(self.rrd_temperature,
                           '--step', str(HEART_BEAT),
                           *data_sources + rra)


app = App()
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/mnt/ramdisk/temperature.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
# This ensures that the logger file handle does not get closed during
# daemonization
daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
