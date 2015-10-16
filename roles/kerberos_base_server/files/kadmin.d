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
# description: Kerberos 5 Kadmin Server
#

. /etc/sysconfig/network

. /etc/init.d/functions

prog="Kerberos 5 Admin Server"

kadmind=/sbin/kadmind

RETVAL=0

start() {
        if [ -f /var/krb5kdc/kpropd.acl ] ; then
            echo $"Error. This appears to be a slave server, found kpropd.acl"
            exit 6
        else
            [ -x $kadmind ] || exit 5
        fi
        echo -n $"Starting $prog: "
        
        daemon ${kadmin} -P /var/run/kadmin.pid
        RETVAL=$?
        
        echo
        [ $RETVAL = 0 ] && touch /var/lock/subsys/kadmin
}
stop() {
        echo -n $"Stopping $prog: "
        killproc ${kadmind}
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && rm -f /var/lock/subsys/kadmin
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
