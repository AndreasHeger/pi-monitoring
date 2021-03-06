#!/bin/bash
# Copyright (c) 2013- Andreas Heger
# All rights reserved.
#
# Author: Andreas Heger, 2013
#
# Please send feedback to 
#
# 
#
# /etc/init.d/monitor_wattson
#
### BEGIN INIT INFO
# Provides: monitor_wattson
# Required-Start: $all
# Should-Start:
# Required-Stop:
# Should-Stop:
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Wattson daemon process
# Description:    Runs up the wattson daemon process
### END INIT INFO

# Activate the python virtual environment
#    . /path_to_virtualenv/activate

case "$1" in
  start)
    echo "Starting server"
    # Start the daemon
    python /usr/share/solar/monitor_wattson.py start
    ;;
  stop)
    echo "Stopping server"
    # Stop the daemon
    python /usr/share/solar/monitor_wattson.py stop
    ;;
  restart)
    echo "Restarting server"
    python /usr/share/solar/monitor_wattson.py restart
    ;;
  *)
    # Refuse to do other stuff
    echo "Usage: /etc/init.d/monitor_wattson {start|stop|restart}"
    exit 1
    ;;
esac

exit 0
