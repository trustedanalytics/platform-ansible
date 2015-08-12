#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# recommended pylint: pylint yarnqueue.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 yarnqueue.py

from ansible.module_utils.basic import *
from cm_api.api_client import ApiResource
from json import loads

CONFIG_KEY = 'yarn_fs_scheduled_allocations'

# this shouldn't be hardcoded...
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
CLUSTER_NAME = "CDH-cluster"

# Default values
DEFAULT_VALUES = {
    'maxMemory': {'key': ['schedulablePropertiesList', 0, 'maxResources', 'memory'], 'default': 1024, 'type': 'int'},
    'maxVCores': {'key': ['schedulablePropertiesList', 0, 'maxResources', 'vcores'], 'default': 2, 'type': 'int'},
    'minMemory': {'key': ['schedulablePropertiesList', 0, 'minResources', 'memory'], 'default': 1024, 'type': 'int'},
    'minVCores': {'key': ['schedulablePropertiesList', 0, 'minResources', 'vcores'], 'default': 2, 'type': 'int'},
    'weight': {'key': ['schedulablePropertiesList', 0, 'weight'], 'default': 1.0, 'type': 'float'},
    'scheduleName': {'key': ['schedulablePropertiesList', 0, 'scheduleName'], 'default': 'default', 'type': None},
    'maxRunningApps': {'key': ['schedulablePropertiesList', 0, 'maxRunningApps'], 'default': 50, 'type': 'int'},
    'schedulingPolicy': {'key': ['schedulingPolicy'], 'default': 'drf', 'type': None},
    'minSharePreemptionTimeout': {'key': ['minSharePreemptionTimeout'], 'default': None, 'type': 'int'},
    'aclSubmitApps': {'key': ['aclSubmitApps'], 'default': '*', 'type': None},
    'aclAdministerApps': {'key': ['aclAdministerApps'], 'default': '*', 'type': None},
    'maxAMShare': {'key': ['schedulablePropertiesList', 'maxAMShare'], 'default': None, 'type': 'int'},
    'impalaMaxRunningQueries': {'key': ['schedulablePropertiesList', 0, 'impalaMaxRunningQueries'], 'default': None, 'type': 'int'},
    'impalaMaxQueuedQueries': {'key': ['schedulablePropertiesList', 0, 'impalaMaxQueuedQueries'], 'default': None, 'type': 'int'},
    'impalaMaxMemory': {'key': ['schedulablePropertiesList', 0, 'impalaMaxMemory'], 'default': None, 'type': 'int'}
}

DOCUMENTATION = '''Script will add new Dynamic Resource Pool to cluster. After \'changed\' status YARN restart is recommended.'''
EXAMPLES = '''yarnqueue: name='Test' ...(params)... -> will create/update queue with specified name.'''

DEFAULT_CONFIG = loads('''{
    "userMaxAppsDefault": null,
    "users": [],
    "fairSharePreemptionTimeout": null,
    "queues": [
        {
            "minSharePreemptionTimeout": null,
            "name": "root",
            "schedulingPolicy": "drf",
            "aclSubmitApps": "*",
            "queues": [
            ],
            "aclAdministerApps": "*",
            "schedulablePropertiesList": [
                {
                    "weight": 1,
                    "maxResources": null,
                    "maxRunningApps": null,
                    "maxAMShare": null,
                    "impalaMaxRunningQueries": null,
                    "scheduleName": "default",
                    "impalaMaxQueuedQueries": null,
                    "impalaMaxMemory": null,
                    "minResources": null
                }
            ]
        }
    ],
    "queueMaxAppsDefault": null,
    "queuePlacementRules": [],
    "defaultQueueSchedulingPolicy": null,
    "defaultMinSharePreemptionTimeout": null,
    "queueMaxAMShareDefault": null
}''')

SAMPLE_NODE = loads('''{
                    "minSharePreemptionTimeout": null,
                    "name": "default",
                    "schedulingPolicy": "drf",
                    "aclSubmitApps": "*",
                    "queues": [],
                    "aclAdministerApps": "*",
                    "schedulablePropertiesList": [
                        {
                            "weight": 1,
                            "maxResources": {
                                "vcores": 1,
                                "memory": 1024
                            },
                            "maxRunningApps": null,
                            "maxAMShare": null,
                            "impalaMaxRunningQueries": null,
                            "scheduleName": "default",
                            "impalaMaxQueuedQueries": null,
                            "impalaMaxMemory": null,
                            "minResources": {
                                "vcores": 1,
                                "memory": 1024
                            }
                        }
                    ]
                }''')


def main():
  argument_spec = dict(name=dict(required=True))

  for key in DEFAULT_VALUES.keys():
    argument_spec[key] = dict(required=False, type=DEFAULT_VALUES[key]['type'])

  module = AnsibleModule(argument_spec=argument_spec)

  api = ApiResource('localhost', username=ADMIN_USER, password=ADMIN_PASS, version=9)

  cluster = api.get_cluster(CLUSTER_NAME)
  service = cluster.get_service('YARN')

  config = service.get_config()[0]

  if CONFIG_KEY not in config.keys():
    config = DEFAULT_CONFIG
  else:
    config = loads(service.get_config()[0][CONFIG_KEY])

  if 'queues' not in config.keys():
    config['queues'] = SAMPLE_NODE['queues']

  # FairScheduler use only root queue
  # script have to find it in provided list from YARN configuration
  for queue in config['queues']:
    if queue['name'] == 'root':
      for root_queue in queue['queues']:
        if root_queue['name'] == module.params.get('name'):
          changed = False
          for param in DEFAULT_VALUES.keys():
            if module.params.get(param) != None:
              curr_node = root_queue
              curr_sample_node = SAMPLE_NODE
              for key in DEFAULT_VALUES[param]['key'][0:-1]:
                if curr_node[key] == None:
                  curr_node[key] = curr_sample_node[key]
                curr_node = curr_node[key]
                curr_sample_node = curr_sample_node[key]
              if curr_node[DEFAULT_VALUES[param]['key'][-1]] != module.params.get(param):
                curr_node[DEFAULT_VALUES[param]['key'][-1]] = module.params.get(param)
                changed = True
          if changed == False:
            module.exit_json(changed=False, msg='Everything is ok ')
          result = service.update_config({CONFIG_KEY: str(config).replace("u'", "'").replace('None', 'null').replace("'", '"')})
          if loads(result[0][CONFIG_KEY]) != config:
            module.fail_json(msg='Error while changing queue settings')
          module.exit_json(changed=True, msg='Updated queue')

      SAMPLE_NODE['name'] = module.params.get('name')

      # change default values of new queue to specified in command parameters
      for param in DEFAULT_VALUES.keys():
        curr_node = SAMPLE_NODE
        if module.params.get(param) != None:
          for key in DEFAULT_VALUES[param]['key'][0:-1]:
            curr_node = curr_node[key]
          if curr_node[DEFAULT_VALUES[param]['key'][-1]] != module.params.get(param):
            curr_node[DEFAULT_VALUES[param]['key'][-1]] = module.params.get(param)
        else:
          curr_node[DEFAULT_VALUES[param]['key'][-1]] = DEFAULT_VALUES[param]['default']
      queue['queues'].append(SAMPLE_NODE)
      result = service.update_config({CONFIG_KEY: str(config).replace("u'", "'").replace('None', 'null').replace("'", '"')})
      if loads(result[0][CONFIG_KEY]) != config:
        module.fail_json(msg='Error while changing queue settings')
      module.exit_json(changed=True, msg='Created queue')
  module.fail_json(msg="Couldn't find root queue")

main()
