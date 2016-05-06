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

set -e

kerberos_enabled=${KERBEROS_ENABLED:-'False'}
push_apps=${PUSH_APPS:-'True'}
platform_ansible_archive=${PLATFORM_ANSIBLE_ARCHIVE:-'https://s3.amazonaws.com/trustedanalytics/platform-ansible-feature-DPNG-6233-new-deployment-apployer.tar.gz'}
tmpdir=$(mktemp -d)

apt-get install -y python-dev python-pip python-virtualenv unzip

virtualenv venv
source venv/bin/activate
pip install ansible==1.9.4 boto six

rm -fr platform-ansible && mkdir -p platform-ansible
pushd platform-ansible

curl -L ${platform_ansible_archive} | tar -xz --strip-components=1

wget --header 'Cookie: oraclelicense=accept-securebackup-cookie' \
  -O ${tmpdir}/UnlimitedJCEPolicyJDK8.zip \
  'http://download.oracle.com/otn-pub/java/jce/8/jce_policy-8.zip' \
  && unzip -u ${tmpdir}/UnlimitedJCEPolicyJDK8.zip \
  -d roles/kerberos_base_common/files/

wget --header 'Cookie: oraclelicense=accept-securebackup-cookie' \
  -O roles/cloudera_base_common/files/java-jdk-1.8.0_72.rpm \
  'http://download.oracle.com/otn-pub/java/jdk/8u72-b15/jdk-8u72-linux-x64.rpm'

wget -O ec2.py 'https://raw.github.com/ansible/ansible/devel/contrib/inventory/ec2.py' \
  && chmod +x ec2.py

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
instance_filters = tag:aws:cloudformation:stack-name=$(awk -F = '{ if ($1 == "stack")  print $2 }' /etc/cfn/cfn-hup.conf)
EOF

cf_password=$(awk -F = '{ if ($1 == "cf_password") print $2 }' /etc/ansible/hosts)
cf_system_domain=$(awk -F = '{ if ($1 == "cf_system_domain") print $2 }' /etc/ansible/hosts)

cat /root/.ssh/id_rsa.pub >>~ubuntu/.ssh/authorized_keys

export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook -e "kerberos_enabled=${kerberos_enabled} install_nginx=False cf_system_domain=${cf_system_domain}" \
  -i ec2.py --skip-tags=one_node_install_only -s tqd.yml

ansible-playbook logsearch.yml

if [ ${push_apps,,} == "true" ]; then
  ansible-playbook -e "kerberos_enabled=${kerberos_enabled} cf_password=${cf_password} cf_system_domain=${cf_system_domain}" -s apployer.yml
fi

popd
