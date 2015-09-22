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
from re import match
from math import pow
try:
  from kazoo.client import KazooClient
  from kazoo.exceptions import AuthFailedError
  from kazoo.security import make_acl, make_digest_acl_credential
  KAZOO_IMPORTED = True
except:
  KAZOO_IMPORTED = False

DOCUMENTATION = ''''''
EXAMPLES = ''''''

MODULE_ARGUMENTS = {
    'dir': {'type': 'str', 'required': True},
    'acl': {'type': 'str', 'required': False},
    'authmethod': {'type': 'str', 'required': False},
    'type': {'type': 'str', 'required': True, 'choices': ['create', 'create_r']},
    'host': {'type': 'str', 'required': True}
}


def get_parent(path):
  return '/'.join([p.replace('/', '') for p in path.split('/')[:-1]])


def get_acl_access_table(acl_access):
  acc_table = {
      # read
      'read': 'r' in acl_access,
      # write
      'write': 'w' in acl_access,
      # create
      'create': 'c' in acl_access,
      # delete
      'delete': 'd' in acl_access,
      # admin
      'admin': 'a' in acl_access
  }
  return acc_table


def get_acl(scheme, credential, acl_access):
  acl_access = get_acl_access_table(acl_access)
  return make_acl(scheme, credential,
                  read=acl_access['read'],
                  write=acl_access['write'],
                  create=acl_access['create'],
                  delete=acl_access['delete'],
                  admin=acl_access['admin'])


# acls are in format <access_type>:<params>:<access>;<next_access>
def generate_acl_list(module, acl_a):
  acl_list = []
  for acl in [a.replace(';', '') for a in acl_a.split(';') if a is not '' and a is not None]:
    acl_data = [a.replace(':', '') for a in acl.split(':') if a is not '']
    acl_access_type = acl_data[0]

    # generate public or ip acl
    if acl_access_type == 'world' or acl_access_type == 'ip':
      acl_list.append(get_acl(acl_access_type, acl_data[1], acl_data[2]))

    # generate acl from username and password
    elif acl_access_type == 'digest':
      acl_list.append(get_acl('digest', make_digest_acl_credential(acl_data[1], acl_data[2]), acl_data[3]))
    else:
      module.fail_json(msg='Unknown acl type: {0}'.format(acl_access_type))
  return acl_list


# create dir if not exists and update acls
def create_dir(module, client, dir_a, acl_list):
  changed = False
  if not client.exists(dir_a):
    changed = True
    try:
      client.create(dir_a, '')
    except Exception as e:
      module.fail_json(msg='Error while creating znode {0} {1}'.format(dir_a, dir(e)))

  # exit execution if acls are not specified
  if acl_list is not None:
    # validate acls
    update_acl = False
    dir_acls = client.get_acls(dir_a)[0]
    if len(dir_acls) is not len(acl_list):
      update_acl = True
    else:
      for acl in dir_acls:
        if acl not in acl_list:
          update_acl = True

    # update acls if validation failed
    if update_acl:
      changed = True
      client.set_acls(dir_a, acl_list)
  return changed


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  host_a = module.params.get('host', None)
  authmethod_a = module.params.get('authmethod', None)
  type_a = module.params.get('type', None)
  dir_a = module.params.get('dir', None)
  acl_a = module.params.get('acl', None)

  # return error if library is not installed
  if not KAZOO_IMPORTED:
    module.fail_json(msg='Kazoo python library is not installed. Use "pip install kazoo" before running script')

  # try connect to zookeeper server
  try:
    client = KazooClient(host_a)
    client.start()
  except:
    module.fail_json(msg='Could not connect to the zookeeper server')

  # add auth method to client
  if authmethod_a is not None:
    try:
      method, username, password = [param.replace(':','') for param in authmethod_a.split(':')]
      if not client.add_auth(method, username + ':' + password):
        module.fail_json(msg='Auth failed')
    except AuthFailedError:
      module.fail_json(msg='Could not auth as specified user')
    except:
      module.fail_json(msg='Param authmethod is not correct')

  # make sure one of setting acls is also used in authmethod and have admin access or is set to world:anyone
  # access can be empty so this acl will be deleted
  if acl_a is not None:
    acl_list = generate_acl_list(module, acl_a)
  else:
    acl_list = None

  # failing if path
  if match('^(/[^ /]+)+$', dir_a) is None:
    module.fail_json(msg='Specified directory does not match zookeeper format')

  changed = False

  # create and update acl for znode
  if type_a == 'create':
    # check if znode parent exists
    if not client.exists(get_parent(dir_a)):
      module.fail_json(msg='Znode {0} parent doesnt exists'.format(dir_a))
    changed = create_dir(module, client, dir_a, acl_list)

  elif type_a == 'create_r':
    path = [a.replace('/', '') for a in dir_a.split('/') if a is not '' and a is not None]
    dir = ''
    for id in range(0, len(path)):
      dir += '/{0}'.format(path[id])

      changed = create_dir(module, client, dir, acl_list) or changed

  # selected type does not match options
  else:
    module.fail_json(msg='Unknown option: {0}'.format(type_a))

  client.stop()
  client.close()
  module.exit_json(changed=changed, msg='Znode and acls match')

main()
