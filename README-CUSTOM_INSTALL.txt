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



Custom installation readme.
Assumption: there is no /dev/vd* devices as we are on the bare metal

I. One node (all in one) installation

1. Configure system with latest CentOS6.x86_64 
2. Make sure you have sufficient amount of memory and disk space
3. Configure 2 paths for data:
 - should be separate mountpoints for better performance 
 - if not, may be any dir, but separate for each datapath
4. Format with ext3 and mount datapaths (add to /etc/fstab as well)
5. Set proper options at defaults/cdh.yml:
 - data paths
6. Set your host on _each_ CDH hostgroup at inventory/cdh
7. Launch bin/one_node_install.sh


II. Bare-metal installation

Assumption: only CDH workers and masters on bare-metal. 

1. Prepare hosts with latest CentOS6.x86_64
2. Make sure you have sufficient amount of memory and disk space
3. Configure 2 paths for data:
 - should be separate mountpoints for better performance
 - if not, may be any dir, but separate for each datapath
4. Check network connectivity between hosts
5. Setup working dns and ntp
6. Format with ext3 and mount datapaths (add to /etc/fstab as well)
7. Set proper options at defaults/cdh.yml:
 - data paths
8. Fill up inventory/cdh with your hosts
9. Launch bin/bare_metal_install.sh
