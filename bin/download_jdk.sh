#!/usr/bin/env bash
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

cd $(dirname $0)/..

url='http://download.oracle.com/otn-pub/java/jdk/8u40-b26/jdk-8u40-linux-x64.rpm'
cookie='Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie'
file='roles/cloudera_base_common/files/java-jdk-1.8.0_40.rpm'

if [ -r "$file" ]; then
  exit 0
fi

while getopts ':u:a' flag; do
  case "${flag}" in
    :) ;;
    u) url=$OPTARG ;;
    a) accept_oracle_license='y' ;;
    \?)
      echo 'Invalid option.' >&2
      exit 1
      ;;
  esac
done

cat <<JCE
Java SE Development Kit (JDK) 1.8.0_40
Download

You must accept the Oracle Binary Code License Agreement for the Java SE
Platform Products (http://www.oracle.com/technetwork/java/javase/terms/license/index.html)
to download this software.

JCE

while [[ $accept_oracle_license != 'y' ]]; do
  cat <<JCE
Accept License Agreement [y/n]
JCE

  read -n 1 -s accept_oracle_license
done

wget --header "$cookie" -O $file $url

if [[ "$?" -ne 0 ]]; then
  echo "Unable to download Java SE Development Kit (JDK) 1.8.0_40" >&2
  exit 1
fi
