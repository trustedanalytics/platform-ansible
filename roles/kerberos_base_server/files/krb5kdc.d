#!/bin/sh
#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# krb5kdc      Start and stop the Kerberos 5 servers.
#
# chkconfig:   - 35 65
# description: Kerberos 5 is a trusted third-party authentication system.
# processname: krb5kdc
# config: /etc/sysconfig/krb5kdc
# pidfile: /var/run/krb5kdc.pid
#

### BEGIN INIT INFO
# Provides: krb5kdc
# Required-Start:
# Required-Stop:
# Should-Start:
# Default-Start:
# Default-Stop: 0 1 2 3 4 5 6
# Short-Description: start and stop the Kerberos 5 KDC
# Description: The krb5kdc is the Kerberos 5 key distribution center, which \
#              issues credentials to Kerberos 5 clients.
### END INIT INFO


. /etc/sysconfig/network

. /etc/init.d/functions

RETVAL=0
prog="Kerberos 5 KDC"
krb5kdc=/sbin/krb5kdc

start() {
        [ -x $krb5kdc ] || exit 5

        echo -n $"Starting $prog: "

        daemon ${krb5kdc} -P /var/run/krb5kdc.pid
        RETVAL=$?

        echo
        [ $RETVAL = 0 ] && touch /var/lock/subsys/krb5kdc
}
stop() {
        echo -n $"Stopping $prog: "
        killproc ${krb5kdc}
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && rm -f /var/lock/subsys/krb5kdc
}

# See how we were called.
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  restart|reload|condrestart)
        stop
        start
        ;;
  status)
        status -l kadmin ${kadmind}
        RETVAL=$?
        ;;
  *)
        echo $"Usage: $0 {start|stop|status|condrestart|reload|restart}"
        RETVAL=2
        ;;
esac

exit $RETVAL
