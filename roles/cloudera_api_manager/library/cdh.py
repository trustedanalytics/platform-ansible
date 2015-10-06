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
# recommended pylint: pylint cdh.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 cdh.py

DOCUMENTATION = '''some documentation'''
EXAMPLES = '''some usage examples'''

from ansible.module_utils.basic import *
from cm_api.api_client import ApiResource, ApiException
from cm_api.endpoints.services import ApiService, ApiServiceSetupInfo
from collections import defaultdict
from subprocess import PIPE, Popen
from time import sleep
from inspect import ismethod
from re import match
from yaml import load
from json import loads

# this shouldn't be hardcoded...
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
CLUSTER_NAME = "CDH-cluster"

# maps for sane service and role names
# since the ones generated by CDH suck
SERVICE_MAP = {
    'hdfs': 'HDFS',
    'zookeeper': 'ZOOKEEPER',
    'hbase': 'HBASE',
    'yarn': 'YARN',
    'hive': 'HIVE',
    'spark': 'SPARK',
    'yarnspark': 'SPARK_ON_YARN',
    'oozie': 'OOZIE',
    'hue': 'HUE',
    'hue-kt': 'HUE',
    'kafka': 'KAFKA',
    'gearpump': 'GEARPUMP',
    'management': '',
    'cm': '',
    'kms': 'KMS',
}

# similar to SERVICE_MAP, but for roles
ROLE_MAP = {
    'zookeeper': 'ZOOKEEPER-SERVER-BASE',
    'datanode': 'HDFS-DATANODE-BASE',
    'namenode': 'HDFS-NAMENODE-BASE',
    'secondarynamenode': 'HDFS-SECONDARYNAMENODE-BASE',
    'activitymonitor': 'mgmt-ACTIVITYMONITOR-BASE',
    'eventserver': 'mgmt-EVENTSERVER-BASE',
    'reportsmanager': 'mgmt-REPORTSMANAGER-BASE',
    'master': 'HBASE-MASTER-BASE',
    'gateway': 'HBASE-GATEWAY-BASE',
    'thrift': 'HBASE-HBASETHRIFTSERVER-BASE',
    'regionserver': 'HBASE-REGIONSERVER-BASE',
    'nodemanager': 'YARN-NODEMANAGER-BASE',
    'metastore': 'HIVE-HIVEMETASTORE-BASE',
    'oozieserver': 'OOZIE-OOZIE_SERVER-BASE',
    'kafka': 'KAFKA-KAFKA_BROKER-BASE',
    'kms': 'KMS-KEY_MANAGEMENT_SERVER',
}

# when creating worker node roles, this map is used to determine the worker role
# of a service and what should it be called
SERVICE_WORKER_MAP = {
    'hbase': {'name': 'REGIONSERVER', 'formatstring': 'HBASE-REGIONSERVER-{0}'},
    'yarn': {'name': 'NODEMANAGER', 'formatstring': 'YARN-NODEMANAGER-{0}'},
    'spark': {'name': 'SPARK_WORKER', 'formatstring': 'SPARK-SPARK_WORKER-{0}'},
    'zookeeper': {'name': 'ZOOKEEPER', 'formatstring': 'ZOOKEEPER-{0}'},
    'kafka': {'name': 'KAFKA_BROKER', 'formatstring': 'KAFKA_BROKER-{0}'},
    'hdfs': {'name': 'DATANODE', 'formatstring': 'HDFS-DATANODE-{0}'},
    'hive': {'name': 'GATEWAY', 'formatstring': 'HIVE-GATEWAY-{0}'},
    'gearpump': {'name': 'GEARPUMP_WORKER', 'formatstring': 'GEARPUMP-GEARPUMP_WORKER-{0}'}
}

# when creating base roles, this map is used to determine what initilization
# functions should be run after creation
SERVICE_INIT_COMMANDS = {
    'HBASE-MASTER': [ApiService.create_hbase_root],
    'SPARK-YARN_HISTORY_SERVER': ['CreateSparkUserDirCommand', 'CreateSparkHistoryDirCommand', 'SparkUploadJarServiceCommand'],
    'OOZIE-OOZIE_SERVER': ['createOozieDb', ApiService.install_oozie_sharelib],
    'HIVE-HIVESERVER2': [ApiService.create_hive_warehouse]
}

# when creating base roles, this map is used to determine what roles are will be
# deployed for a given service
BASE_SERVICE_ROLE_MAP = {
    'hbase': {
        'HBASE-HBASETHRIFTSERVER': 'HBASETHRIFTSERVER',
        'HBASE-GATEWAY': 'GATEWAY',
        'HBASE-MASTER': 'MASTER'
    },
    'yarn': {
        'YARN-RESOURCEMANAGER': 'RESOURCEMANAGER',
        'YARN-JOBHISTORY': 'JOBHISTORY',
        'YARN-GATEWAY': 'GATEWAY'
    },
    'hive': {
        'HIVE-HIVEMETASTORE': 'HIVEMETASTORE',
        'HIVE-HIVESERVER2': 'HIVESERVER2',
        'HIVE-WEBHCAT': 'WEBHCAT'
    },
    'yarnspark': {
        'SPARK-YARN_HISTORY_SERVER': 'SPARK_YARN_HISTORY_SERVER',
        'SPARK-GATEWAY': 'GATEWAY'
    },
    'spark': {
        'SPARK-SPARK_MASTER': 'SPARK_MASTER',
        'SPARK-GATEWAY': 'GATEWAY'
    },
    'oozie': {
        'OOZIE-OOZIE_SERVER': 'OOZIE_SERVER'
    },
    'hue': {
        'HUE-HUE_SERVER': 'HUE_SERVER'
    },
    'hue-kt': {
        'HUE-KT_RENEWER': 'KT_RENEWER'
    },
    'gearpump': {
        'GEARPUMP-GEARPUMP_WEBUI': 'GEARPUMP_WEBUI',
        'GEARPUMP-GEARPUMP_MASTER': 'GEARPUMP_MASTER'
    },
    'kms': {
        'KMS-KEY_MANAGEMENT_SERVER': 'KMS'
    }
}

# arguments that the module gets in various actions
MODULE_ARGUMENTS = ['action', 'host', 'name', 'nn_host', 'jn1_host', 'jn2_host', 'jn3_host', 'role', 'entity', 'state', 'service', 'sn_host', 'value', 'version', 'license', 'params']


def main():
  module = AnsibleModule(argument_spec=dict((argument, {'type': 'str'}) for argument in MODULE_ARGUMENTS))

  api = ApiResource('localhost', username=ADMIN_USER, password=ADMIN_PASS, version=9)
  cluster_name = CLUSTER_NAME

  manager = api.get_cloudera_manager()

  action_a = module.params.get('action', None)

  if action_a == 'create_cluster':
    license_a = module.params.get('license', None)
    version_a = module.params.get('version', None)

    cluster_list = [x.name for x in api.get_all_clusters()]
    if cluster_name in cluster_list:
      module.exit_json(changed=False, msg='Cluster exists')
    else:
      cluster = api.create_cluster(CLUSTER_NAME, fullVersion=version_a)
      if license_a == None:
        manager.begin_trial()
      else:
        manager.update_license(license_a.decode('base64'))
      module.exit_json(changed=True, msg='Cluster created')
  elif action_a in ['add_host', 'create_mgmt', 'deploy_parcel', 'deploy_hdfs_base', 'deploy_hdfs_dn', 'deploy_hdfs_ha', 'deploy_rm_ha', 'set_config', 'service', 'deploy_service', 'deploy_service_worker_nodes', 'deploy_base_roles', 'run_command', 'cluster','create_snapshot_policy']:
    # more complicated actions that need a created cluster go here
    cluster = api.get_cluster(cluster_name)
    host_map = dict((api.get_host(x.hostId).hostname, x.hostId) for x in cluster.list_hosts())

    # adds a host to the cluster
    # host_name should be in the internal DNS format, ip-xx-xx-xx.copute.internal
    if action_a == 'add_host':
      host_a = module.params.get('host', None)

      host_list = host_map.keys()
      if host_a in host_list:
        module.exit_json(changed=False, msg='Host already in cluster')
      else:
        try:
          cluster.add_hosts([host_a])
        except ApiException:
          # if a host isn't there, it could be because the agent didn't manage to connect yet
          # so let's wait a moment for it
          sleep(120)
          cluster.add_hosts([host_a])

        module.exit_json(changed=True, msg='Host added')

    # create management service and set it's basic configuration
    # this needs a separate function since management is handled
    # differently than the rest of services
    elif action_a == 'create_mgmt':
      host_a = module.params.get('host', None)

      # getting the management service is the only way to check if mgmt exists
      # an exception means there isn't one
      try:
        mgmt = manager.get_service()
        module.exit_json(changed=False, msg='Mgmt service already exists')
      except ApiException:
        pass

      mgmt = manager.create_mgmt_service(ApiServiceSetupInfo())

      # this is ugly... and I see no good way to unuglify it
      firehose_passwd = Popen("sudo grep com.cloudera.cmf.ACTIVITYMONITOR.db.password /etc/cloudera-scm-server/db.mgmt.properties | awk -F'=' '{print $2}'", shell=True, stdout=PIPE).stdout.read().rstrip("\n")
      reports_passwd = Popen("sudo grep com.cloudera.cmf.REPORTSMANAGER.db.password /etc/cloudera-scm-server/db.mgmt.properties | awk -F'=' '{print $2}'", shell=True, stdout=PIPE).stdout.read().rstrip("\n")

      # since there is no easy way of configuring the manager... let's do it here :(
      role_conf = defaultdict(dict)
      role_conf['ACTIVITYMONITOR'] = {
          'firehose_database_host': '{0}:7432'.format(host_a),
          'firehose_database_user': 'amon',
          'firehose_database_password': firehose_passwd,
          'firehose_database_type': 'postgresql',
          'firehose_database_name': 'amon',
          'firehose_heapsize': '268435456',
      }
      role_conf['EVENTSERVER'] = {
          'event_server_heapsize': '215964392'
      }
      role_conf['REPORTSMANAGER'] = {
          'headlamp_database_host': '{0}:7432'.format(host_a),
          'headlamp_database_user': 'rman',
          'headlamp_database_password': reports_passwd,
          'headlamp_database_type': 'postgresql',
          'headlamp_database_name': 'rman',
          'headlamp_heapsize': '215964392',
      }

      roles = ['ACTIVITYMONITOR', 'ALERTPUBLISHER', 'EVENTSERVER', 'HOSTMONITOR', 'SERVICEMONITOR', 'REPORTSMANAGER']
      # create mangement roles
      for role in roles:
        mgmt.create_role('{0}-1'.format(role), role, host_map[host_a])

      # update configuration of each
      for group in mgmt.get_all_role_config_groups():
        group.update_config(role_conf[group.roleType])

      mgmt.start().wait()
      # after starting this service needs time to spin up
      sleep(30)
      module.exit_json(changed=True, msg='Mgmt created and started')

    # deploy a given parcel on all hosts in the cluster
    # you can specify a substring of the version ending with latest, for example 5.3-latest instead of 5.3.5-1.cdh5.3.5.p0.4
    elif action_a == 'deploy_parcel':
      name_a = module.params.get('name', None)
      version_a = module.params.get('version', None)

      if "latest" in version_a:
        available_versions = [x.version for x in cluster.get_all_parcels() if x.product == name_a]
        if "-latest" in version_a:
          version_substr = match('(.+?)-latest', version_a).group(1)
        # if version is just "latest", try to check everything
        else:
          version_substr = ".*"
        try:
          [version_parcel] = [x for x in available_versions if re.match(version_substr, x) != None]
        except ValueError:
          module.fail_json(msg='Specified version {0} doesnt appear in {1} or appears twice'.format(version_substr, available_versions))
      else:
        version_parcel = version_a

      # we now go through various stages of getting the parcel
      # as there is no built-in way of waiting for an operation to complete
      # we use loops with sleep to get it done
      parcel = cluster.get_parcel(name_a, version_parcel)
      if parcel.stage == 'AVAILABLE_REMOTELY':
        parcel.start_download()

        while parcel.stage != 'DOWNLOADED':
          parcel = cluster.get_parcel(name_a, version_parcel)
          if parcel.state.errors:
            raise Exception(str(parcel.state.errors))
          sleep(10)

      if parcel.stage == 'DOWNLOADED':
        parcel.start_distribution()

        while parcel.stage != 'DISTRIBUTED':
          parcel = cluster.get_parcel(name_a, version_parcel)
          if parcel.state.errors:
            raise Exception(str(parcel.state.errors))
          # sleep while hosts report problems after the download
          for i in range(12):
            sleep(10)
            if sum([1 for x in api.get_all_hosts(view='Full') if x.healthSummary != 'GOOD']) == 0:
              break

      # since parcels are distributed automatically when a new host is added to a cluster
      # we can encounter the ,,ACTIVATING'' stage then
      if parcel.stage == 'DISTRIBUTED' or parcel.stage == 'ACTIVATING':
        if parcel.stage == 'DISTRIBUTED':
          parcel.activate()

        while parcel.stage != 'ACTIVATED':
          parcel = cluster.get_parcel(name_a, version_parcel)
          # this sleep has to be large because although the operation is very fast
          # it makes the management and cloudera hosts go bonkers, failing all of the health checks
          sleep(10)

        # sleep while hosts report problems after the distribution
        for i in range(60):
          sleep(10)
          if sum([1 for x in api.get_all_hosts(view='Full') if x.healthSummary != 'GOOD']) == 0:
            break

        module.exit_json(changed=True, msg='Parcel activated')

      if parcel.stage == 'ACTIVATED':
        module.exit_json(changed=False, msg='Parcel already activated')

      # if we get down here, something is not right
      module.fail_json(msg='Invalid parcel state')

    # deploy nodes for workers, according to SERVICE_WORKER_MAP
    # also give them sane names and init zookeeper and kafka ones
    # which need id's specified
    elif action_a == 'deploy_service_worker_nodes':
      host_a = module.params.get('host', None)
      service_a = module.params.get('service', None)

      service_name = SERVICE_MAP[service_a]
      role_name = SERVICE_WORKER_MAP[service_a]['name']
      full_role_name = SERVICE_WORKER_MAP[service_a]['formatstring']

      if not service_name in [x.name for x in cluster.get_all_services()]:
        service = cluster.create_service(service_name, service_name)
      else:
        service = cluster.get_service(service_name)

      nodes = [x for x in service.get_all_roles() if role_name in x.name]

      # if host already has the given group, we should skip it
      if host_map[host_a] in [x.hostRef.hostId for x in nodes]:
        module.exit_json(changed=False, msg='Host already is a {0}'.format(role_name))
      # find out the highest id that currently exists
      else:
        node_names = [x.name for x in nodes]
        if len(node_names) == 0:
          # if no nodes, start numbering from 1
          node_i = 1
        else:
          # take the max number and add 1 to it
          node_i = max([int(x.split('-')[-1]) for x in node_names]) + 1

        if service_name == 'ZOOKEEPER':
          role = service.create_role(full_role_name.format(node_i), 'SERVER', host_a)
          # zookeeper needs a per-node ID in the configuration, so we set it now
          role.update_config({'serverId': node_i})
        elif service_name == 'KAFKA':
          role = service.create_role(full_role_name.format(node_i), role_name, host_a)
          # kafka needs a per-node ID in the configuration, so we set it now
          role.update_config({'broker.id': node_i})
        else:
          service.create_role(full_role_name.format(node_i), role_name, host_a)

        module.exit_json(changed=True, msg='Added host to {0} role'.format(role_name))

    # deploy a service. just create it, don't do anything more
    # this is needed maily when we have to set service properties before role deployment
    elif action_a == 'deploy_service':
      name_a = module.params.get('name', None)

      if not name_a in SERVICE_MAP:
        module.fail_json(msg='Unknown service: {0}'.format(name_a))
      service_name = SERVICE_MAP[name_a]
      if not service_name in [x.name for x in cluster.get_all_services()]:
        service = cluster.create_service(service_name, service_name)
        module.exit_json(changed=True, msg='{0} service created'.format(service_name))
      else:
        module.exit_json(changed=False, msg='{0} service already exists'.format(service_name))

    # deploy the base hdfs roles (the namenode and secondary)
    # this doesn't create the service, as at least one datanode should already be added!
    # the format also requires certain properties to be set before we run it
    elif action_a == 'deploy_hdfs_base':
      nn_host_a = module.params.get('nn_host', None)
      sn_host_a = module.params.get('sn_host', None)

      changed = False

      hdfs = cluster.get_service('HDFS')
      hdfs_roles = [x.name for x in hdfs.get_all_roles()]

      # don't create a secondary namenode when:
      #- there is one that already exists
      #- there is a second namenode, which means we have HA and don't need a secondary
      if not 'HDFS-SECONDARYNAMENODE' in hdfs_roles and not 'HDFS-NAMENODE-2' in hdfs_roles:
        hdfs.create_role('HDFS-SECONDARYNAMENODE', 'SECONDARYNAMENODE', sn_host_a)
        changed = True

      # create a namenode and format it's FS
      # formating the namenode requires at least one datanode and secondary namenode already in the cluster!
      if not 'HDFS-NAMENODE' in hdfs_roles:
        hdfs.create_role('HDFS-NAMENODE', 'NAMENODE', nn_host_a)
        for command in hdfs.format_hdfs('HDFS-NAMENODE'):
          if command.wait().success == False:
            module.fail_json(msg='Failed formating HDFS namenode with error: {0}'.format(command.resultMessage))
        changed = True

      module.exit_json(changed=changed, msg='Created HDFS service & NN roles')

    # enable HA for HDFS
    # this deletes the secondary namenode and creates a second namenode in it's place
    # also, this spawns 3 journal node and 2 failover controller roles
    elif action_a == 'deploy_hdfs_ha':
      sn_host_a = module.params.get('sn_host', None)
      jn_names_a = [module.params.get('jn1_host', None), module.params.get('jn2_host', None), module.params.get('jn3_host', None)]

      hdfs = cluster.get_service('HDFS')

      # if there's a second namenode, this means we already have HA enabled
      if not 'HDFS-NAMENODE-2' in [x.name for x in hdfs.get_all_roles()]:
        # this is bad and I should feel bad
        # jns is a list of dictionaries, each dict passes the required journalnode parameters
        jns = [{'jnHostId': host_map[jn_name], 'jnEditsDir': '/data0/hadoop/journal', 'jnName': 'HDFS-JOURNALNODE-{0}'.format(i + 1)} for i, jn_name in enumerate(jn_names_a)]

        # this call is so long because we set some predictable names for the sevices
        command = hdfs.enable_nn_ha('HDFS-NAMENODE', host_map[sn_host_a], 'nameservice1', jns, zk_service_name='ZOOKEEPER',
                                    active_fc_name='HDFS-FAILOVERCONTROLLER-1', standby_fc_name='HDFS-FAILOVERCONTROLLER-2', standby_name='HDFS-NAMENODE-2')

        children = command.wait().children
        for command_children in children:
          # The format command is expected to fail, since we already formated the namenode
          if command_children.name != 'Format' and command.success == False:
            module.fail_json(msg='Command {0} failed when enabling HDFS HA with error {1}'.format(command_children.name, command_children.resultMessage))
        module.exit_json(changed=True, msg='Enabled HA for HDFS service')
      else:
        module.exit_json(changed=False, msg='HDFS HA already enabled')
    # enable HA for YARN
    elif action_a == 'deploy_rm_ha':
      sn_host_a = module.params.get('sn_host', None)

      yarn = cluster.get_service('YARN')

      # if there are two roles matching to this name, this means HA for YARN is enabled
      if len([0 for x in yarn.get_all_roles() if match('^YARN-RESOURCEMANAGER.*$', x.name) != None]) == 1:
        command = yarn.enable_rm_ha(sn_host_a, zk_service_name='ZOOKEEPER')
        children = command.wait().children
        for command_children in children:
          if command.success == False:
            module.fail_json(msg='Command {0} failed when enabling YARN HA with error {1}'.format(command_children.name, command_children.resultMessage))
        module.exit_json(changed=True, msg='Enabled HA for YARN service')
      else:
        module.exit_json(changed=False, msg='YARN HA already enabled')

    # deploy the base roles for a service, according to BASE_SERVICE_ROLE_MAP
    # after the deployments run commands specified in BASE_SERVICE_ROLE_MAP
    elif action_a == 'deploy_base_roles':
      host_a = module.params.get('host', None)
      service_a = module.params.get('service', None)

      service_name = SERVICE_MAP[service_a]
      changed = False

      if not service_name in [x.name for x in cluster.get_all_services()]:
        service = cluster.create_service(service_name, service_name)
      else:
        service = cluster.get_service(service_name)

      service_roles = [x.name for x in service.get_all_roles()]

      # create each service from the map
      for (role_name, cloudera_name) in BASE_SERVICE_ROLE_MAP[service_a].items():
        # check if role already exists, script cant compare it directly
        # after enabling HA on YARN roles will have random strings in names
        if len([0 for x in service_roles if match(role_name, x) != None]) == 0:
          service.create_role(role_name, cloudera_name, host_a)
          changed = True

          # init commmands
          if role_name in SERVICE_INIT_COMMANDS.keys():
            for command_to_run in SERVICE_INIT_COMMANDS[role_name]:
              # different handling of commands specified by name and
              # ones specified by an instance method
              if ismethod(command_to_run):
                command = command_to_run(service)
              else:
                command = service.service_command_by_name(command_to_run)

              if command.wait().success == False:
                module.fail_json(msg='Running {0} failed with {1}'.format(command_to_run, command.resultMessage))

      if changed == True:
        module.exit_json(changed=True, msg='Created base roles for {0}'.format(service_name))
      else:
        module.exit_json(changed=False, msg='{0} base roles already exist'.format(service_name))

    # set config values for a given service/role
    elif action_a == 'set_config':
      entity_a = module.params.get('entity', None)
      service_a = module.params.get('service', None)
      role_a = module.params.get('role', None)
      name_a = module.params.get('name', None)
      value_a = module.params.get('value', None)

      if not service_a in SERVICE_MAP:
        module.fail_json(msg='Unknown service: {0}'.format(service_a))

      # since management is handled differently, it needs a different service
      if service_a == 'management':
        service = manager.get_service()
      elif service_a == 'cm':
        service = manager
      else:
        service = cluster.get_service(SERVICE_MAP[service_a])

      # role and service configs are handled differently
      if entity_a == 'service':
        prev_config = service.get_config()
        curr_config = service.update_config({name_a: value_a})
        if service_a == 'cm':
          prev_config = [prev_config]
          curr_config = [curr_config]
        module.exit_json(changed=(str(prev_config[0]) != str(curr_config[0])), msg='Config value for {0}: {1}'.format(name_a, curr_config[0][name_a]))

      elif entity_a == 'role':
        if not role_a in ROLE_MAP:
          module.fail_json(msg='Unknown role: {0}'.format(service))

        role = service.get_role_config_group(ROLE_MAP[role_a])
        prev_config = role.get_config()
        curr_config = role.update_config({name_a: value_a})
        module.exit_json(changed=(str(prev_config) != str(curr_config)), msg='Config value for {0}: {1}'.format(name_a, curr_config[name_a]))

      else:
        module.fail_json(msg='Invalid entity, must be one of service, role')

    # handle service state
    # currently this only can start/restart a service
    elif action_a == 'service':
      state_a = module.params.get('state', None)
      service_a = module.params.get('service', None)

      try:
        if service_a == 'cm':
          service = manager.get_service()
        else:
          service = cluster.get_service(SERVICE_MAP[service_a])
      except ApiException:
        module.fail_json(msg='Service does not exist')

      # when starting a service, we also deploy the client config for it
      if state_a == 'started':
        if service.serviceState == 'STARTED':
          module.exit_json(changed=False, msg='Service already running')
        method = service.start
        verb = "start"
      elif state_a == 'restarted':
        method = service.restart
        verb = "restart"

      try:
        command = service.deploy_client_config()
        if command.wait().success == False:
          module.fail_json(msg='Deploying client config failed with {0}'.format(command.resultMessage))
      # since there is no way to check if a service handles client config deployments
      # we try our best and pass the exception if it doesn't
      except ApiException, AttributeError:
        pass

      method().wait()
      # we need to wait for cloudera checks to complete...
      # otherwise it will report as failing
      sleep(10)
      for i in range(24):
        sleep(10)
        service = manager.get_service() if service_a == "cm" else cluster.get_service(SERVICE_MAP[service_a])
        if service.serviceState == 'STARTED' and service.healthSummary == 'GOOD':
          break
      service = manager.get_service() if service_a == "cm" else cluster.get_service(SERVICE_MAP[service_a])
      if service.serviceState == 'STARTED' and service.healthSummary == 'GOOD':
        module.exit_json(changed=True, msg='Service {0} successful'.format(verb))
      else:
        module.fail_json(msg='Service {0} failed'.format(verb))

    # handle cluster
    # currently this only can restart
    elif action_a == 'cluster':
      state_a = module.params.get('state', None)

      if state_a == 'restarted':
        command = cluster.restart(redeploy_client_configuration=True)
        if command.wait().success == False:
          module.fail_json(msg='Cluster resart failed with {0}'.format(command.resultMessage))
        else:
          module.exit_json(changed=True, msg='Cluster restart successful')

    # Snapshot policy
    # only create is supported
    elif action_a == 'create_snapshot_policy':
      name_a = module.params.get('name', None)
      value_a = module.params.get('value', None)
      service_a = module.params.get('service', None)
      service = cluster.get_service(SERVICE_MAP[service_a])
      payload=loads(value_a)
      # checking if policy already exists. Exception is expected when configure for the first time.
      try: 
        test = service.get_snapshot_policy(name_a)
        module.exit_json(changed=False, msg='Defined policy already exists')
      except ApiException:
        pass
      try:
        command = service.create_snapshot_policy(payload)
        module.exit_json(changed=True, msg='Snapshot policy was created.')
      except ApiException, AttributeError:
        module.fail_json(msg='ERROR in creating snapshot policy.')

    elif action_a == 'run_command':
      service_a = module.params.get('service', None)
      name_a = module.params.get('name', None)
      params_a = module.params.get('params', None)

      params = load(params_a) if params_a else {}

      # since management is handled differently, it needs a different service
      if service_a == 'management':
        service = manager.get_service()
      elif service_a == 'cm':
        service = manager
      elif not SERVICE_MAP[service_a] in [x.name for x in cluster.get_all_services()]:
        module.fail_json(msg='Service {0} doesn\'t exist!'.format(SERVICE_MAP[service_a]))
      else:
        service = cluster.get_service(SERVICE_MAP[service_a])

      command = service._cmd(name_a, params=params)
      if command.wait().success == False:
        module.fail_json(msg='Running {0} failed with {1}'.format(name_a, command.resultMessage))
      else:
        module.exit_json(changed=True, msg='Command {0} ran succesfully'.format(name_a))

  else:
    module.fail_json(msg='Invalid action')

main()