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

WORK_DIR="/var/krb5kdc"
EXT_SERVER="$WORK_DIR/extensions.kdc"
CAKEY="$WORK_DIR/cakey.pem"
CACERT="$WORK_DIR/cacert.pem"
KDCKEY="$WORK_DIR/kdckey.pem"
KDCREQ="$WORK_DIR/kdc.req"
KDCPEM="$WORK_DIR/kdc.pem"
SUCCESS="$WORK_DIR/PKINIT_SUCCESS"

REALM=$1

if [ $# -lt 1 ]; then
  echo "Can not find realm name"
  exit 1
fi

if ! [ -e $WORK_DIR ]; then
  mkdir -p $WORK_DIR || exit $?
fi

# Secure krb folder
chmod 755 $WORK_DIR
chown root:root $WORK_DIR

# Do not regenerate certs by mistake
if [ -r $SUCCESS ]; then
  echo "SUCCESS"
  exit 0
fi

if ! [ -e $EXT_SERVER ]; then
  echo "Cannot find $EXT_SERVER"
  exit 1
fi

openssl genrsa -out $CAKEY 2048 || exit $?
echo -e "\n\n\n\n\n\n\n" | openssl req -key $CAKEY -new -x509 -out $CACERT -days 3650 || exit $?

openssl genrsa -out $KDCKEY 2048 || exit $?
echo -e "\n\n\n\n\n\n\n\n\n\n\n" | openssl req -new -out $KDCREQ -key $KDCKEY || exit $?

env REALM=$REALM openssl x509 -req -in $KDCREQ \
    -CAkey $CAKEY -CA $CACERT -out $KDCPEM -days 365 \
    -extfile $EXT_SERVER -extensions kdc_cert -CAcreateserial || exit $?

echo "Created"
# After success touch file
touch $SUCCESS
exit 0
