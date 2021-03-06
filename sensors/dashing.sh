#!/bin/bash

# See: https://github.com/mivok/squirrelpouch/wiki/dashing-pi
# Dashing service
# Add this file to /etc/init.d/
# $ sudo cp dashboard /etc/init.d/
# Update variables DASHING_DIR, GEM_HOME, & PATH to suit your installation
# $ sudo nano /etc/init.d/dashboard
# Make executable
# $ sudo chmod 755 /etc/init.d/dashboard
# Update rc.d
# $ sudo update-rc.d dashboard defaults
# Dashboard will start at boot. Check out the boot log for trouble shooting "/var/log/boot.log"
# USAGE: start|stop|status|logs

### BEGIN INIT INFO
# Provides:          dashboard
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

set -e

# Must be a valid filename
NAME=dashing
DASHING_DIR=/mnt/ramdisk/dashboard/
DAEMON=/usr/local/bin/dashing
DASHING_USER=www-data
PIDFILE="$DASHING_DIR/$NAME.pid"
DAEMON_OPTS="start -d -P $PIDFILE"
GEM_HOME=/var/lib/gems/1.9.1

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games

case "$1" in
  start)
    echo -n "Starting daemon: "$NAME
    start-stop-daemon --start --quiet --chdir $DASHING_DIR --chuid $DASHING_USER --exec $DAEMON -- $DAEMON_OPTS
    echo "."
  ;;
  stop)
    echo -n "Stopping daemon: "$NAME
    start-stop-daemon --stop --quiet --signal 9 --oknodo --pidfile $PIDFILE
    echo "."
  ;;
  restart)
    start-stop-daemon --stop --quiet --signal 9 --oknodo --retry 30 --pidfile $PIDFILE
    start-stop-daemon --start --quiet --chdir $DASHING_DIR --chuid $DASHING_USER --exec $DAEMON -- $DAEMON_OPTS
    echo "."
  ;;
  logs)
    echo "See the logs of the Dashing."
    tail -f $DASHING_DIR'log/thin.log'
  ;;

  *)
  echo "Usage: "$1" {start|stop|restart}"
  exit 1
esac

exit 0
