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
# chkconfig: -
# description: Kerberos 5 KDC
#

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
