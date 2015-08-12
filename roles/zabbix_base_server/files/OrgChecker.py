#!/usr/bin/env python
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



import sys
import subprocess
import json

#wykonuje komende w shellu
def execut(cmd):
        proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        proc.wait()
        return out

def executAsOrg(api,cmd):
        return execut('alias cfo="CF_HOME=/.cf/'+api.replace(' ','')+'/ cf" \n cfo '+cmd)

def parseToJson(api,cmd):
        return json.loads(executAsOrg(api,cmd))

if(len(sys.argv)!=4):
        print('Error')
        sys.exit('')

api=sys.argv[3]
org=sys.argv[2]
type=sys.argv[1]

lorg=parseToJson(api,"curl /v2/organizations?q=name:"+org)

lorg2 = lorg['resources'][0]['metadata']['guid']

mt=parseToJson(api,'curl '+lorg['resources'][0]['entity']['quota_definition_url'])

MAX=0
if(type=='1'):
        MAX=int(mt['entity']['memory_limit'])
        URL='/v2/apps?q=organization_guid:'+lorg2+'&order-direction=asc&results-per-page=100'
elif(type=='2'):
        MAX=int(mt['entity']['total_routes'])
        URL='/v2/routes?q=organization_guid:'+lorg2
elif(type=='3'):
        Spaces=''
        for x in parseToJson(api,'curl '+lorg['resources'][0]['entity']['spaces_url'])['resources']:
                if(Spaces!=''):
                        Spaces+=','
                Spaces+=str(x['metadata']['guid'])

        URL='/v2/service_instances?q=space_guid+IN+'+Spaces+''

        MAX=int(mt['entity']['total_services'])
else:
        sys.exit('eerror')


RES=0

Res=True

Page=1;
while(Res):
        app=parseToJson(api,'curl '+URL+'&page='+str(Page))
        Page+=1
        Res=Page<int(app['total_pages'])
        if(type=='2' or type=='3'):
                Res=False
                RES+=int(app['total_results'])
        elif(type=='1'):
                for x in app['resources']:
                        RES+=int(x['entity']['memory'])*int(x['entity']['instances'])

print float(RES)/MAX*100
