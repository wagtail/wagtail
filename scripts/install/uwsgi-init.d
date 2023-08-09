#!/usr/bin/env bash

### BEGIN INIT INFO
# Provides:          emperor
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: uwsgi for wagtail
# Description:       uwsgi for wagtail
### END INIT INFO
set -e


PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin
DAEMON=/usr/local/bin/uwsgi
RUN=/var/run/uwsgi
CONFIG_DIR=/etc/uwsgi/vassals
NAME=uwsgi
DESC=emperor
OWNER=root
GROUP=root
OP=$1

[[ -x $DAEMON ]] || exit 0
[[ -d $RUN ]] || mkdir $RUN && chown $OWNER.$GROUP $RUN


do_pid_check()
{
    local PIDFILE=$1
    [[ -f $PIDFILE ]] || return 0
    local PID=$(cat $PIDFILE)
    for p in $(pgrep $NAME); do
        [[ $p == $PID ]] && return 1
    done
    return 0
}


do_start()
{
    local PIDFILE=$RUN/$NAME.pid
    local START_OPTS=" \
        --emperor $CONFIG_DIR \
        --pidfile $PIDFILE \
        --uid $OWNER --gid $GROUP \
        --daemonize /var/log/$NAME/uwsgi-emperor.log"
    if do_pid_check $PIDFILE; then
        $NAME $START_OPTS
    else
        echo "Already running!"
    fi
}

send_sig()
{
    local PIDFILE=$RUN/$NAME.pid
    set +e
    [[ -f $PIDFILE ]] && kill $1 $(cat $PIDFILE) > /dev/null 2>&1
    set -e
}

wait_and_clean_pidfile()
{
    local PIDFILE=$RUN/uwsgi.pid
    until do_pid_check $PIDFILE; do
        echo -n "";
    done
    rm -f $PIDFILE
}

do_stop()
{
    send_sig -3
    wait_and_clean_pidfile
}

do_reload()
{
    send_sig -1
}

case "$OP" in
    start)
        echo "Starting $DESC: "
        do_start
        echo "$NAME."
        ;;
    stop)
        echo -n "Stopping $DESC: "
        do_stop
        echo "$NAME."
        ;;
    reload)
        echo -n "Reloading $DESC: "
        do_reload
        echo "$NAME."
        ;;
    restart)
        echo  "Restarting $DESC: "
        do_stop
        sleep 1
        do_start
        echo "$NAME."
        ;;
    *)
        N=/etc/init.d/$NAME
        echo "Usage: $N {start|stop|restart|reload}">&2
        exit 1
        ;;
esac
exit 0