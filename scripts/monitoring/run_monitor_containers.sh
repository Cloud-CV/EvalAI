#!/bin/bash
path=$PWD
webhook_url=''
env='staging'
if [ ! -z "$1" ]
  then
    path=$1
fi

if [ ! -z "$2" ]
  then
    webhook_url=$2
fi

if [ ! -z "$3" ]
  then
    env=$3
fi

# crontab doesn't have access to env variable, define explicitly
export MONITORING_SLACK_WEBHOOK_URL=${webhook_url};
export ENV=${env};

python ${path}/scripts/monitoring/monitor_containers.py
