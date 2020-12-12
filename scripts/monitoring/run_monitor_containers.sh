#!/bin/bash
path=$PWD
if [ ! -z "$1" ]
  then
    path=$1
fi

# crontab doesn't have access to env variable, define explicitly
export MONITORING_SLACK_WEBHOOK_URL=x;

python ${path}/scripts/monitoring/monitor_containers.py
