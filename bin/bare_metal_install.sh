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
echo -e "\n\nYou are trying to start BARE-METAL install.\n\n
If unsure refer to online documentation at:
https://github.com/trustedanalytics/platform-wiki/wiki/Hybrid-Deployment-(OpenStack-&-bare-metal)
\n\nPress Ctrl-C to abort in 30s.\n\n"
sleep 30;

export ANSIBLE_HOST_KEY_CHECKING=False
exec ansible-playbook site.yml -v -i inventory/cdh -f 20 -s --skip-tags=skip_on_bare_metal -v
