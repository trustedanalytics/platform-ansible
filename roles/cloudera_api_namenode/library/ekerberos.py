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
# recommended pylint: pylint ekerberos.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 ekerberos.py

DOCUMENTATION = '''This module will create refresh kerberos principal for specified user on his own account if it will expire in next 15 min.'''
EXAMPLES = '''
You have to specify user and password for kerberos

  - name: Refresh
    ekerberos: usr='root' pass='kerberos_password'
'''

from ansible.module_utils.basic import *
from subprocess import PIPE, Popen
from datetime import datetime, timedelta
from re import match

# arguments that the module gets in various actions
MODULE_ARGUMENTS = {
    'usr': {'type': 'str', 'required': True},
    'pass': {'type': 'str', 'required': True}
}


def execute(cmd):
  proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  out, err = proc.communicate()
  proc.wait()
  return out, err


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  # script will only set password at start, at creation time. If you want change it you have to delete user at start
  usr_a = module.params.get('usr', None)
  pass_a = module.params.get('pass', None)
  std_o, err_o = execute('sudo -u "{0}" klist'.format(usr_a))
  kerberos_renew = False
  if std_o == '' or (err_o != None and err_o != ''):
    kerberos_renew = True
  else:
    std_lines = [a.replace('\n', '').replace('\t', '') for a in std_o.split('\n')]
    if match('^Default principal: {0}@.*$'.format(usr_a), std_lines[1]) == None:
      kerberos_renew = True
    else:
      # Extracting principal expire date
      expire_date = 'T'.join([a.replace(' ', '').replace('/', ':') for a in std_lines[-3].split(' ')][3:5])
      # Checking if principal will expire in next 15 minutes or is already expired
      if datetime.now() > datetime.strptime(expire_date, '%m:%d:%yT%H:%M:%S') - timedelta(minutes=15):
        kerberos_renew = True
  if kerberos_renew:
    std_o, err_o = execute('echo -e "{1}\n" | sudo -u "{0}" kinit "{0}"'.format(usr_a, pass_a))
    if err_o != None and err_o != '':
      module.fail_json(msg='Something is wrong with kerberos ')
  module.exit_json(changed=kerberos_renew, msg='Everything is done ')

main()
