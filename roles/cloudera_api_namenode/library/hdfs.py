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

#
# recommended pylint: pylint hdfs.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 hdfs.py

DOCUMENTATION = '''This module works like \'dir\' module'''
EXAMPLES = ''''''

from ansible.module_utils.basic import *
from subprocess import PIPE, Popen

# arguments that the module gets in various actions
MODULE_ARGUMENTS = {
    'dir': {'type': 'str', 'required': True},
    'owner': {'type': 'str'},
    'group': {'type': 'str'},
    'mode': {'type': 'str'}
}


def execute(cmd):
  proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  out, err = proc.communicate()
  proc.wait()
  if proc.returncode == 0:
    err = None
  return out, err


def executehdfs(cmd):
  return execute('sudo -u hdfs hdfs dfs -' + cmd)


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  dir_a = module.params.get('dir', None)
  owner_a = module.params.get('owner', None)
  group_a = module.params.get('group', None)
  mode_a = module.params.get('mode', None)

  # extracting folder parent location
  dir_handler = [a for a in dir_a.split('/') if a != '']
  if len(dir_handler) < 2:
    curr_path = '/'
  else:
    curr_path = '/' + '/'.join(dir_handler[0:-1])
    if curr_path[-1] != '/':
      curr_path += '/'
  current_dir = dir_handler[-1]

  changed = False
  std_o, err_o = executehdfs('ls hdfs:{0} | grep {0}{1}'.format(curr_path, current_dir))
  if std_o == '' or std_o == None:
    # here we will create catalog
    std_o, err_o = executehdfs('mkdir {0}{1}'.format(curr_path, current_dir))
    if err_o != None and err_o != '':
      module.fail_json(msg='Error when creating {0}{1} file. Error: {2}'.format(curr_path, current_dir, err_o))
    std_o, err_o = executehdfs('ls hdfs:{0} | grep "{0}{1}$"'.format(curr_path, current_dir))
    if std_o == None or std_o == '':
      module.fail_json(msg='Folder {0} doesnt exists or you dont have access'.format(curr_path))
    changed = True

  if std_o[0] != 'd':
    module.fail_json(msg='File {0} is not directory'.format(curr_path, current_dir))

  state_data = [a for a in std_o.split(' ') if a != '']

  # parsing privileges from drwxrwxrwx to chmod 777 format
  privileges = ''
  for i in range(0, 3):
    privileges_tmp = 0
    tmp = 4
    for j in range(0, 3):
      if std_o[1 + i * 3 + j] != '-':
        privileges_tmp += tmp
      tmp /= 2
    privileges += str(privileges_tmp)

  # changing privileges if it is different than specified in parameters
  # ignoring case when user did not specify this parameter
  if privileges != mode_a and mode_a != None:
    std_o, err_o = executehdfs('chmod {0} hdfs:{1}{2}'.format(mode_a, curr_path, current_dir))
    if err_o != '' and err_o != None:
      module.fail_json(msg='Folder {0}{1} chmod error. Error: {2}'.format(curr_path, current_dir, err_o))
    changed = True

  # changing owner and group if it is different than specified in parameters
  # ignoring case when user did not specify this parameters
  if (owner_a != state_data[2] and owner_a != None) or (group_a != state_data[3] and group_a != None):
    # changing values from None to current in hdfs
    if owner_a == None:
      owner_a = state_data[2]
    if group_a == None:
      group_a = state_data[3]
    std_o, err_o = executehdfs('chown {0}:{1} hdfs:{2}{3}'.format(owner_a, group_a, curr_path, current_dir))
    if err_o != '' and err_o != None:
      module.fail_json(msg='Folder {0}{1} chown error. Error: {2}'.format(curr_path, current_dir, err_o))
    changed = True

  # Validating data not req
  module.exit_json(changed=changed, msg='Everything is done')

main()
