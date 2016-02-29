#!/usr/bin/env bash

# Fill CLUSTER and API with proper values

_CLUSTER="CDH-cluster-name"
API="http://user:pass@host:7180"

LOGFILE="TAP-CDH-"`date +'%Y-%m-%d_%H%M'`

## DO NOT EDIT BELOW

CLUSTER=$(echo ${_CLUSTER} | sed -e "s/ /%20/")

if ! (jq --version >/dev/null) || ! (curl --version >/dev/null); then 
  echo -e "\n You need jq and curl packages to perform this command.\n\n Try: 'yum install jq curl' or 'apt-get install jq curl' \n\n"; 
  exit 1; 
fi

# Inventory
echo -e "\n\n CM version\n" >> ${LOGFILE}
curl -s ${API}/api/v10/cm/version | jq  . >> ${LOGFILE}

echo -e "\n\n CM roles\n" >> ${LOGFILE}
curl -s ${API}/api/v10/cm/service/roles | jq . >> ${LOGFILE}

echo -e "\n\n CDH inventory\n" >> ${LOGFILE}
curl -s ${API}/api/v10/hosts?view=full | jq  . >> ${LOGFILE}

# CM
echo -e "\n\nNon default settings for CM\n" >> ${LOGFILE}
curl -s ${API}/api/v10/cm/config | jq . >> ${LOGFILE}

# SERVICES

for i in $(curl -s ${API}/api/v10/clusters/${CLUSTER}/services |jq -M ".items | .[] | .name" | sed 's/"//g'); do
	echo -e "\nNon default settings for ${i}:\n" >> ${LOGFILE}
	curl -s ${API}/api/v10/clusters/${CLUSTER}/services/${i}/config | jq . >> ${LOGFILE}
done

echo -e "\n\nPlease send results (file: ${LOGFILE}) to TAP team.\n\n"
