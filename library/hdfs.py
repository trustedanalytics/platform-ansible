#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 Intel Corporation
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

# recommended pylint: pylint hdfs.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 hdfs.py

import os.path
from subprocess import PIPE, Popen
from ansible.module_utils.basic import *

DOCUMENTATION = '''
This module provides two functionalities:
1) when dir and optionally group, mode, owner parameters are provided it creates a directory in hdfs and
optionally sets permissions and ownership for it
2) when src, dst and optionally group, mode, owner parameters are provided it copies a file from local fs
to an existing directory in hdfs and optionally sets permissions and ownership for it
'''
EXAMPLES = '''
1) hdfs: dir=/user/oozie group=oozie mode=750 owner=oozie -> directory is created in hdfs and permissions
along with ownership are set
2) hdfs: src=/etc/service.conf dst=/user/oozie/service.conf group=oozie mode=640 owner=oozie -> file
is copied from local filesystem to an existing dirextory in hdfs and permissions along with ownership are set
'''

MODULE_ARGUMENTS = {
    'dir': {'type': 'str'},
    'owner': {'type': 'str'},
    'group': {'type': 'str'},
    'mode': {'type': 'str'},
    'src': {'type': 'str'},
    'dst': {'type': 'str'}
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


def hdfs_create_directory(module, directory, owner=None, group=None, mode=None):
  """Creates a directory in hdfs and optionally sets ownership and permissions for it"""
  changed = False
  dir_handler = [a for a in directory.split('/') if a != '']
  if len(dir_handler) < 2:
    curr_path = '/'
  else:
    curr_path = '/' + '/'.join(dir_handler[0:-1])
  if curr_path[-1] != '/':
    curr_path += '/'
  current_dir = dir_handler[-1]

  std_o, err_o = executehdfs('ls hdfs:{0} | grep {0}{1}'.format(curr_path, current_dir))
  if std_o == '' or std_o is None:
    std_o, err_o = executehdfs('mkdir {0}{1}'.format(curr_path, current_dir))
    if err_o is not None and err_o != '':
      module.fail_json(msg='Error when creating {0}{1} file. Error: {2}'.format(curr_path, current_dir, err_o))
    changed = True

  std_o, err_o = executehdfs('ls hdfs:{0} | grep "{0}{1}$"'.format(curr_path, current_dir))
  if std_o[0] != 'd':
    module.fail_json(msg='File {0}{1} is not directory'.format(curr_path, current_dir))

  state_data = [a for a in std_o.split(' ') if a != '']

  privileges = ''
  for i in range(0, 3):
    privileges_tmp = 0
    tmp = 4
    for j in range(0, 3):
      if std_o[1 + i * 3 + j] != '-':
        privileges_tmp += tmp
      tmp /= 2
    privileges += str(privileges_tmp)

  if privileges != mode and mode is not None:
    std_o, err_o = executehdfs('chmod {0} hdfs:{1}{2}'.format(mode, curr_path, current_dir))
    if err_o != '' and err_o is not None:
      module.fail_json(msg='Folder {0}{1} chmod error. Error: {2}'.format(curr_path, current_dir, err_o))
    changed = True

  if (owner != state_data[2] and owner is not None) or (group != state_data[3] and group is not None):
    if owner is None:
      owner = state_data[2]
    if group is None:
      group = state_data[3]
    std_o, err_o = executehdfs('chown {0}:{1} hdfs:{2}{3}'.format(owner, group, curr_path, current_dir))
    if err_o != '' and err_o is not None:
      module.fail_json(msg='Folder {0}{1} chown error. Error: {2}'.format(curr_path, current_dir, err_o))
    changed = True

  return changed


def hdfs_put_file(module, source, destination, owner=None, group=None, mode=None):
  """Puts a local file to an existing directory in hdfs and optionally sets ownership and permissions for it"""
  changed = False
  put_needed = False
  if not os.path.isfile(source):
    module.fail_json(msg='Local file {0} does not exist'.format(source))
  std_o, err_o = executehdfs('ls hdfs://{0}'.format(destination))
  if err_o is not None:
    put_needed = True
  elif err_o is None:
    std_o_2, err_o_2 = executehdfs('du hdfs://{0}'.format(destination))
    if err_o_2 != '' and err_o_2 is not None:
      module.fail_json(msg='File hdfs://{0} du error. Error: {1}'.format(destination, err_o_2))
    du_size_hdfs = int(std_o_2.split(' ')[0])
    du_size_local = os.path.getsize(source)
    if du_size_hdfs != du_size_local:
      put_needed = True
      std_o_2, err_o_2 = executehdfs('rm hdfs://{0}'.format(destination))
  elif err_o != '':
    module.fail_json(msg='File hdfs://{0} ls file. Error: {1}'.format(destination, err_o))

  if put_needed:
    std_o, err_o = executehdfs('put {0} hdfs://{1}'.format(source, destination))
    if err_o != '' and err_o is not None:
      module.fail_json(msg='Put of local {0} to hdfs://{1} error. Error: {2}'.format(source, destination, err_o))
    changed = True

  if owner is not None or group is not None or mode is not None:
    std_o, err_o = executehdfs('ls hdfs://{0}'.format(destination))
    if err_o is not None and err_o != '':
      module.fail_json(msg='File hdfs://{0} ls file. Error: {1}'.format(destination, err_o))
    ls_data = std_o
    state_data = [a for a in std_o.split(' ') if a != '']

    if (owner != state_data[2] and owner is not None) or (group != state_data[3] and group is not None):
      if owner is None:
        owner = state_data[2]
      if group is None:
        group = state_data[3]
      std_o, err_o = executehdfs('chown {0}:{1} hdfs://{2}'.format(owner, group, destination))
      if err_o != '' and err_o is not None:
        module.fail_json(msg='File hdfs://{0} chown error. Error: {1}'.format(destination, err_o))
      changed = True

    if mode is not None:
      privileges = ''
      for i in range(0, 3):
        privileges_tmp = 0
        tmp = 4
        for j in range(0, 3):
          if ls_data[1 + i * 3 + j] != '-':
            privileges_tmp += tmp
          tmp /= 2
        privileges += str(privileges_tmp)

      if privileges != mode:
        std_o, err_o = executehdfs('chmod {0} hdfs://{1}'.format(mode, destination))
        if err_o != '' and err_o is not None:
          module.fail_json(msg='Fle hdfs://{0} chmod error. Error: {1}'.format(destination, err_o))
        changed = True

  return changed


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  changed = False
  dir_a = module.params.get('dir', None)
  owner_a = module.params.get('owner', None)
  group_a = module.params.get('group', None)
  mode_a = module.params.get('mode', None)
  src_a = module.params.get('src', None)
  dst_a = module.params.get('dst', None)

  if dir_a is not None:
    changed = hdfs_create_directory(module, dir_a, owner_a, group_a, mode_a)
  elif src_a is not None and dst_a is not None:
    changed = hdfs_put_file(module, src_a, dst_a, owner_a, group_a, mode_a)
  else:
    module.fail_json(msg='At least dir or src/dst parameters should be set for module')

  module.exit_json(changed=changed, msg='Everything is done')

main()
