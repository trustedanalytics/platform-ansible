#!/usr/bin/env bash
#
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

# !!! READ THIS !!!
#
# Applying this upgrade will stop and reboot your
# nodes, therefore it requires a proper maintenance
# window of at least 3 hours.
#
# Usage:
# - make sure CDH cluster state is "green"
# - backup any mission-critical data (i.e. HDFS, docker DBMS)
# - backup all ELK data, the upgrade process will clear all indices
# - login to JumpBox machine and become root
# - use any kind of terminal virtualization, i.e. tmux, screen
# - copy this very upgrade script to /root/upgrade_to_v0.7.4.1.sh
# - run as root:
#          chmod +x /root/upgrade_to_v0.7.4.1.sh; /root/upgrade_to_v0.7.4.1.sh
# - monitor the progress, if the command fails, repeat it
# - as a result, all your nodes, including JumpBox, will be rebooted

set -e

export ANSIBLE_HOST_KEY_CHECKING=False

release_version='v0.7.4.1'
platform_ansible_archive=${PLATFORM_ANSIBLE_ARCHIVE:-"https://github.com/trustedanalytics/platform-ansible/archive/${release_version}.tar.gz"}
kerberos_enabled=${KERBEROS_ENABLED:-'False'}
kubernetes_enabled=${KUBERNETES_ENABLED:-'False'}
provider=$(awk -F= '/^provider/{print $2}' /etc/ansible/hosts)

cd /root
rm -fr platform-ansible && mkdir -p platform-ansible
pushd platform-ansible
curl -L ${platform_ansible_archive} |tar -xz --strip-components=1

if [ ${provider} == 'aws' ]; then
  wget -O ec2.py 'https://raw.github.com/ansible/ansible/devel/contrib/inventory/ec2.py' \
	  && chmod +x /root/platform-ansible/ec2.py

cat <<EOF >ec2.ini
[ec2]
regions = all
regions_exclude = us-gov-west-1,cn-north-1
destination_variable = private_dns_name
vpc_destination_variable = private_ip_address
route53 = False
rds = False
elasticache = False
cache_path = ~/.ansible/tmp
cache_max_age = 300
instance_filters = tag:aws:cloudformation:stack-name=$(awk -F= '/^stack/{print $2}' /etc/cfn/cfn-hup.conf)
EOF

  ansible-playbook -i ec2.py -s upgrade_to_${release_version}.yml \
    -e "provider=${provider} kerberos_enabled=${kerberos_enabled} kubernetes_enabled=${kubernetes_enabled} release_version=${release_version}"

elif [ ${provider} == 'openstack' ]; then

  cloudera_masters=$(awk -F= '/^cloudera_masters/{print $2}' /etc/ansible/hosts)
  cloudera_workers=$(awk -F= '/^cloudera_workers/{print $2}' /etc/ansible/hosts)

  if [ -n "${no_proxy}" ]; then
    if [ -z "${cloudera_masters}" ]; then
      seq 1 254 | while read a;
      do
        no_proxy=${no_proxy},10.0.5.$a
      done
    else
      no_proxy=${no_proxy},${cloudera_workers},${cloudera_masters}
    fi
  fi

  wget -O openstack.py 'https://raw.github.com/ansible/ansible/devel/contrib/inventory/openstack.py' \
	   && chmod +x /root/platform-ansible/openstack.py

  ansible-playbook -i openstack.py -s upgrade_to_${release_version}.yml \
    -e "provider=${provider} kerberos_enabled=${kerberos_enabled} kubernetes_enabled=${kubernetes_enabled} release_version=${release_version} no_proxy=${no_proxy}"

fi

popd
