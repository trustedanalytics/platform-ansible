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


#Do zmiany hasel dostepowych do api zmienic zawartosc pliku /.cf/{api}/.DefaultPass



import sys
import subprocess
import os


def execut(cmd):
        proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        proc.wait()
        return out


def validate(file):
        with open(file,'r') as f:
                lines=f.readlines()
        if(len(lines)<2):
                return False
        return True

def getData(file):
        with open(file,'r') as f:
                lines=f.readlines()
        return lines[0].replace('\n',''),lines[1].replace('\n','')

if(len(sys.argv)==2):

        FOLDER='/.cf/'+sys.argv[1].replace(' ','')+'/'
        CONFIG=FOLDER+'.DefaultPass'
        if(os.path.exists(FOLDER)==False):
                os.mkdir(FOLDER)
        if(os.path.exists(CONFIG)==False or validate(CONFIG)==False):
                sys.exit('Error')

        LOGIN,PASS=getData(CONFIG)

        if(execut('alias cfo="CF_HOME=/.cf/'+sys.argv[1].replace(' ','')+'/ cf" \n cfo login -a '+sys.argv[1]+' -u "'+LOGIN+'" -p "'+PASS+'" -o default -s default').split('\n')[2]!='OK'):
                sys.exit('error')
        U=[a.replace(' ','') for a in execut('alias cfo="CF_HOME=/.cf/'+sys.argv[1].replace(' ','')+'/ cf" \n cfo orgs').split('\n')[3:] if a is not '']
        RES='{"data":['
        K=False
        for a in U:
                if(K):
                        RES+=','
                RES+='{"{#ORG}":"'+a+'"}'
                K=True


        RES+=']}'
        print(RES)
else:
        print('Error')
