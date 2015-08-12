#!/bin/bash
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


#arg2: env name

#argument options:
# a: check API endpoint
# l: check login
# o: list orgs
# S: list spaces
# A: list apps
# d: dump app log
# s: check app status

export 'CF_HOME=/.cf/cfm/'$2


CREDENTIALSFILE='/.cf/'$2'/.DefaultPass'

i=0
while read p; do
		CREDENTIALS[i]=$p
		let i=i+1
    done < $CREDENTIALSFILE



#config files

#orgs [org]
ORGS='/.cf/cfm/'$2'/orgs'
#spaces [org:space]
SPACES='/.cf/cfm/'$2'/spaces'
#apps [org:space:app]
APPS='/.cf/cfm/'$2'/apps'

while getopts "alosAdS" o
do      case $o in
        a)  cf api $2
            ;;

        l)  cf api $2
            cf auth  ${CREDENTIALS[0]} ${CREDEDENTIALS[1]}
            ;;

        o)  cf orgs
            ;;
        S)  while read p; do
                cf target -o $p
		cf spaces
            done < $ORGS
            ;;

        A)  while read p; do
                org=(`echo $p | cut -f 1 -d ':'`)
                space=(`echo $p | cut -f 2 -d ':'`)
                cf target -o $org -s $space
                cf apps
            done < $SPACES
            ;;

        d)  while read p; do
                org=(`echo $p | cut -f 1 -d ':'`)
                space=(`echo $p | cut -f 2 -d ':'`)
                app=(`echo $p | cut -f 3 -d ':'`)
                cf target -o $org -s $space
                cf logs --recent $app
            done < $APPS
            ;;

        s)  while read p; do
                org=(`echo $p | cut -f 1 -d ':'`)
                space=(`echo $p | cut -f 2 -d ':'`)
                app=(`echo $p | cut -f 3 -d ':'`)
                cf target -o $org -s $space
                cf app $app
            done < $APPS
            ;;
        [?])    print  "Wrong arguments."
                exit 1;;
        esac
done



