#!/bin/bash
path=$PWD
auth_token=''
api_host_url=''
if [ ! -z "$1" ]
  then
    path=$1
fi

if [ ! -z "$2" ]
  then
    auth_token=$2
fi

if [ ! -z "$3" ]
  then
    api_host_url=$3
fi

if [ ! -z "$4" ]
  then
    env=$4
fi

# crontab doesn't have access to env variable, define explicitly
export AUTH_TOKEN=${auth_token};
export API_HOST_URL=${api_host_url};
export ENV=${env}

/home/ubuntu/venv/bin/python ${path}/scripts/monitoring/auto_scale_workers.py
