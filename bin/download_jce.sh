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

url='http://download.oracle.com/otn-pub/java/jce/7/UnlimitedJCEPolicyJDK7.zip'
file=$(mktemp -d)/UnlimitedJCEPolicyJDK7.zip
exdir=roles/kerberos_base_common/files
accept_oracle_license='n'

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
Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy Files 7
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

wget --header 'Cookie: oraclelicense=accept-securebackup-cookie' -O $file $url
if [[ "$?" -ne 0 ]]; then
  echo "Unable to download Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy Files 7" >&2
  exit 1
fi

unzip -u $file -d $exdir
if [[ "$?" -ne 0 ]]; then
  echo "Unable to unzip Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy Files 7" >&2
  exit 1
fi

rm -fr $(dirname $file)
