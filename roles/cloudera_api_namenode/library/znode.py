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
# recommended pylint: pylint znode.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 znode.py

from ansible.module_utils.basic import *
from subprocess import PIPE, Popen
from re import match

DOCUMENTATION = '''This module will create znodes in ZooKeeper'''
EXAMPLES = '''
To create znode use:
  - name: Create znode
    znode: dir='Test'

This script can also create whole path:

  - name: Create znode
    znode: dir='Test/Test/Test'
'''

# arguments that the module gets in various actions
MODULE_ARGUMENTS = {
    'dir': {'type': 'str', 'required': True}
}


def execute(cmd):
  proc = Popen('hbase zkcli ' + cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  out, err = proc.communicate()
  proc.wait()
  if match('.*ERROR.*', err, re.S + re.M) == None:
    err = None
  return out, err


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)
  # script will only set password at start, at creation time. If you want change it you have to delete user at start
  dir_a = module.params.get('dir', None)
  dir_list = [a for a in dir_a.split('/') if a != '']
  current_dir = '/'
  changed = False
  # creating whole path of this znode
  for folder in dir_list:
    std_o, err_o = execute('ls {0} | tail -n1 | grep "^\\["'.format(current_dir))
    if err_o != '' and err_o != None:
      module.fail_json(msg='Some error with zookeeper: ' + err_o)
    if std_o != None and std_o != '':
      list_of_dirs = std_o.replace('[', '').replace(']', '').replace('\n', '').replace(' ', '').split(',')
      if folder not in list_of_dirs:
        if current_dir[-1] != '/':
          current_dir += '/'
        std_o, err_o = execute('create {0}{1} null'.format(current_dir, folder))
        changed = True
    if current_dir[-1] != '/':
      current_dir += '/'
    current_dir += folder
  module.exit_json(changed=changed, msg='Everything is done ')

main()
