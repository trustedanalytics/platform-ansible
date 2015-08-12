#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# recommended pylint: pylint edhbase.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 edhbase.py

DOCUMENTATION = '''This module will create tables/namespaces in hbase'''
EXAMPLES = '''
To create table:

Script will only create table if it doesn't exists. HBase command looks like 'create name, params', eg.

  create ‘t1′, {NAME => ‘f1′, VERSIONS => 1, TTL => 2592000, BLOCKCACHE => true}

In ansible it should look like this:

 - name: Creating table
   edhbase: type=table name='t1' params='{NAME => ‘f1′, VERSIONS => 1, TTL => 2592000, BLOCKCACHE => true}'

IF you want to add table to namespace use:

 - name: Creating table
   edhbase: type=table name='t1' params='{NAME => ‘f1′, VERSIONS => 1, TTL => 2592000, BLOCKCACHE => true}' namespace='test_namespace'

To create namespace:

 - name: Creating namespace
   edhbase: type=namespace name='test_namespace' state='create'

To remove namespace:

 - name: Creating namespace
   edhbase: type=namespace name='test_namespace' state='remove'

To set namespace config option:

 - name: Creating namespace
   edhbase: type=namespace name='test_namespace' state='set' option='xxx' value='xxx'

To unset namespace config option:

 - name: Creating namespace
   edhbase: type=namespace name='test_namespace' state='set' option='xxx'
'''

from ansible.module_utils.basic import *
from subprocess import PIPE, Popen
from re import match

# arguments that the module gets in various actions
MODULE_ARGUMENTS = {'type': {'type': 'str', 'required': True},
                    'state': {'type': 'str', 'required': True},
                    'name': {'type': 'str', 'required': True},
                    'option': {'type': 'str'},
                    'value': {'type': 'str'},
                    'namespace': {'type': 'str'},
                    'params': {'type': 'str'}}


def executehbase(cmd):
  cmd = 'echo -e "{0}\\nexit" | sudo -u hbase hbase shell'.format(cmd)
  proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  out, err = proc.communicate()
  proc.wait()
  return out, err


def listresults(cmd, delimiter):
  std_o, err_o = executehbase(cmd)
  if "ERROR" in std_o:
    return -1
  if match('.*{0}.*'.format(delimiter), std_o, re.M + re.S + re.I) == None:
    return 0
  return 1


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  type_a = module.params.get('type', None)
  state_a = module.params.get('state', None)
  name_a = module.params.get('name', None)
  option_a = module.params.get('option', None)
  value_a = module.params.get('value', None)
  namespace_a = module.params.get('namespace', None)
  params_a = module.params.get('params', None)

  if type_a == 'namespace':
    result = listresults('list_namespace', '^' + name_a + '$')
    # error with kerberos or hbase api
    if result == -1:
      module.fail_json(msg='Some error with HBase')
    elif state_a == 'create':
      if result == 0:
        # executing different commands depending on if params parameter is set
        if params_a == None:
          result = "ERROR" in executehbase("create_namespace '{0}'".format(name_a))[0]
        else:
          result = "ERROR" in executehbase("create_namespace '{0}', {1}".format(name_a, params_a))[0]

        if result:
          module.fail_json(msg='Error while creating namespace')
        else:
          module.exit_json(changed=True, msg='Namespace created')
      else:
        module.exit_json(changed=False, msg='Namespace exists')
    elif state_a == 'remove':
      # removing namespace if it exists
      if result == 1:
        if "ERROR" in executehbase("drop_namespace '{0}'".format(name_a))[0]:
          module.fail_json(msg='Error while deleting namespace')
        else:
          module.exit_json(changed=True, msg='Namespace deleted')
      else:
        module.exit_json(changed=False, msg='Namespace doesnt exists')
    elif state_a == 'set':
      if option_a == None:
        module.fail_json(msg='Require option')
      if value_a == None:
        # checking if option is already set
        result = listresults("describe_namespace '{0}'".format(name_a), option_a + " =>")
        if result == 1:
          if "ERROR" in executehbase("alter_namespace '{0}', {METHOD => 'unset', name_a => '{1}'}".format(name_a, option_a))[0]:
            module.fail_json(msg='Error when unsetting value')
          else:
            module.exit_json(changed=True, msg='Namespace modified')
        else:
          module.exit_json(changed=False, msg='Namespace up-to-date')
      else:
        result = listresults("describe_namespace '{0}'".format(name_a), "{0} => '{1}'".format(option_a, value_a))
        if result == 1:
          module.exit_json(changed=False, msg='Namespace up-to-date')
        else:
          if "ERROR" in executehbase("alter_namespace '{0}', {METHOD => 'set', '{1}' => '{2}'}".format(name_a, option_a, value_a))[0]:
            module.fail_json(msg='Error while setting value')
          else:
            module.exit_json(changed=True, msg='Namespace modified')

  # creating table without namespace
  elif type_a == 'table' and namespace_a == None:
    result = listresults('list', '^' + name_a + '$')
    if result == -1:
      module.fail_json(msg='Some error with HBase')
    elif state_a == 'create':
      if params_a == None:
        module.fail_json(msg='Params required')
      if result == 0:
        if "ERROR" in executehbase("create '{0}', {1}".format(name_a, params_a))[0]:
          module.fail_json(msg='Error while creating table')
        else:
          module.exit_json(changed=True, msg='Table created')
      else:
        module.exit_json(changed=False, msg='Table exists')

  # creating table in namespace
  elif type_a == 'table':
    result = listresults("list_namespace_tables '{0}'".format(namespace_a), '^' + name_a + '$')
    if result == -1:
      module.fail_json(msg='Some error with HBase')
    elif state_a == 'create':
      if params_a == None:
        module.fail_json(msg='Params required')
      if result == 0:
        if "ERROR" in executehbase("create '{0}':'{1}', {2}'".format(namespace_a, name_a, params_a))[0]:
          module.fail_json(msg='Error while creating table')
        else:
          module.exit_json(changed=True, msg='Table created')
      else:
        module.exit_json(changed=False, msg='Table exists')

main()
