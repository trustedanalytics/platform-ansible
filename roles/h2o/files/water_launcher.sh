#!/bin/bash
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

# usage: water_launcher.sh <nodecount> <noderam>

if [ ! -z $1 ]; then
  NODES_NUMBER=$1
else
  NODES_NUMBER=2
fi
if [ ! -z $2 ]; then
  NODE_MEMORY=$2
else
  NODE_MEMORY="1g"
fi

UUID="`uuidgen`"
TMP_DIR="/tmp/h2o/$UUID"
OUTPUT_DIR="/h2o/$UUID"
NOTIFY_FILE="$TMP_DIR/h2o_notify.txt"
TIMEOUT="60"
H2OUSER="h2ouser"
H2OPASS="h2opass"

if [ -f .water-driver ]; then
  . .water-driver
fi

mkdir -p $TMP_DIR && hadoop jar water-driver.jar -username $H2OUSER -password $H2OPASS -timeout $TIMEOUT -nodes $NODES_NUMBER -mapperXmx $NODE_MEMORY -output $OUTPUT_DIR -notify $NOTIFY_FILE -disown
