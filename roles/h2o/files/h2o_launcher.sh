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

# usage: h2o_launcher.sh <nodecount>

if [ ! -z $1 ]; then
  NODES_NUMBER=$1
else
  NODES_NUMBER=2
fi
UUID="`uuidgen`"
TMP_DIR="/tmp/h2o/$UUID"
OUTPUT_DIR="/h2o/$UUID"
NOTIFY_FILE="$TMP_DIR/h2o_notify.txt"

mkdir -p $TMP_DIR && hadoop jar h2odriver.jar -nodes $NODES_NUMBER -mapperXmx 1g -output $OUTPUT_DIR -notify $NOTIFY_FILE -disown
