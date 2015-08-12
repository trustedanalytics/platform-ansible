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


import requests

import json

import sys


if len(sys.argv) == 1:
    # print 'Options: \n -s : check services \n -h : check hosts \n -m : check
    # manager service'
    sys.exit(1)

OUTPUT = '{0}: {1}'


clusters = requests.get(
    'http://admin:admin@{0}:7180/api/v9/clusters'.format(
        sys.argv[1]), auth=(
            'admin', 'admin'))

name = json.loads(clusters.text)['items'][0]['name']

result = 'Critical'

description = ' '

if '-s' in sys.argv:
    description += 'Hadoop Services ( '
    # services
    services = requests.get(
        'http://admin:admin@{0}:7180/api/v9/clusters/{1}/services'.format(
            sys.argv[1], name), auth=(
            'admin', 'admin'))
    items = json.loads(services.text)['items']

    if items:
        for item in items:
            description += '{0}:{1} '.format(
                item['name'],
                item['healthSummary'])

        result = 'OK'

        if 'BAD' in description:
            result = 'Critical'

        if 'NOT_AVAILABLE' in description:
            result = 'Critical'

        if 'CONCERNING' in description:
            result = 'Concerning'

    else:
        description += 'no CDH services available'

if '-h' in sys.argv:
    description += 'Hosts ( '
    # hosts
    hosts = requests.get(
        'http://admin:admin@{0}:7180/api/v9/hosts?view=full'.format(
            sys.argv[1]), auth=(
            'admin', 'admin'))
    hostList = json.loads(hosts.text)['items']

    if hostList:
        for host in hostList:
            description += '{0}:{1} '.format(
                host['hostname'],
                host['healthSummary'])

        result = 'OK'

        if 'BAD' in description:
            result = 'Critical'

        if 'NOT_AVAILABLE' in description:
            result = 'Critical'

        if 'CONCERNING' in description:
            result = 'Concerning'

    else:
        description += 'no CDH hosts available'


if '-m' in sys.argv:
    description += 'Manager Service Status ( '
    # manager service status
    manager_status = requests.get(
        'http://admin:admin@{0}:7180/api/v9/cm/service'.format(
            sys.argv[1]), auth=(
            'admin', 'admin'))

    manager_service_status = json.loads(manager_status.text)

    description += '{0}:{1} '.format(
        manager_service_status['name'],
        manager_service_status['healthSummary'])

    result = 'OK'

    if 'BAD' in description:
        result = 'Critical'

    if 'NOT_AVAILABLE' in description:
        result = 'Critical'

    if 'CONCERNING' in description:
        result = 'Concerning'

description += ')'


print OUTPUT.format(result, description)


status = 2

if result == 'OK':
    status = 0

sys.exit(status)
