#!/usr/bin/env python
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


import sys
import datetime
import subprocess
import json

type = sys.argv[1]
db = sys.argv[2]

end = datetime.datetime.now()
start = end - datetime.timedelta(0, 300)

cmd = 'aws cloudwatch get-metric-statistics --metric-name ' + type + \
    ' --period 300 --dimensions Name=DBInstanceIdentifier,Value=' + db + \
    ' --statistics Average --namespace AWS/RDS --start-time ' + \
    start.strftime('%Y-%m-%dT%H:%M:%S') + ' --end-time ' + \
    end.strftime('%Y-%m-%dT%H:%M:%S')

proc = subprocess.Popen(
    cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

out, err = proc.communicate()

proc.wait()

if (out == ''):
    print('Error > aws w')
    sys.exit()

js = json.loads(out)

value = js['Datapoints'][0]['Average']

print(value)
