#!/usr/bin/python
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

# -*- coding: utf-8 -*-
#
# recommended pylint: pylint kadduser.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 kadduser.py

DOCUMENTATION = '''This module will add user principals to kerberos if it doesn't exists. It wont change password if user already exist in kerberos.'''
EXAMPLES = '''
- name: add user
  kadduser: name='root' password='kerberos_password'
'''

from ansible.module_utils.basic import *
from subprocess import PIPE, Popen

# arguments that the module gets in various actions
MODULE_ARGUMENTS = {
    'name': {'type': 'str', 'required': True},
    'password': {'type': 'str', 'required': True}
}


def execute(cmd, scnd_command=None):
  cmd = 'kadmin.local -q "{0}" '.format(cmd)
  if scnd_command != None:
    cmd += ' | {0}'.format(scnd_command)
  proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  out, err = proc.communicate()
  proc.wait()
  return out, err


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  # script will only set password at start, at creation time. If you want change it you have to delete user before script start
  name_a = module.params.get('name', None)
  password_a = module.params.get('password', None)

  std_o, err_o = execute('list_principals', ' grep "{0}@"'.format(name_a))
  if err_o != '' and err_o != None:
    module.fail_json(msg='Kerberos error {0}'.format(err_o))
  changed = False

  # checking if principal elready exist
  if std_o == '' or std_o == None:
    std_o, err_o = execute('addprinc -pw "{1}" "{0}"'.format(name_a, password_a))
    if err_o != '' and err_o != None and err_o[0] != 'W':
      module.fail_json(msg='Kerberos error {0}'.format(err_o))
    changed = True
  module.exit_json(changed=changed, msg='Everything is done')

main()
