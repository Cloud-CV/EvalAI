#!/bin/bash
path=$PWD
auth_token=''
api_host_url=''

cluster_name='evalai-production-workers'
range_days=0.21
period_seconds=60

if [ ! -z "$1" ]; then
  path=$1
fi

if [ ! -z "$2" ]; then
  auth_token=$2
fi

if [ ! -z "$3" ]; then
  api_host_url=$3
fi

if [ ! -z "$4" ]; then
  json_path=$4
fi

if [ ! -z "$5" ]; then
  cluster_name=$5
fi

if [ ! -z "$6" ]; then
  range_days=$6
fi

if [ ! -z "$7" ]; then
  period_seconds=$7
fi

export AUTH_TOKEN=${auth_token}
export API_HOST_URL=${api_host_url}
export JSON_PATH=${json_path}

/home/ubuntu/venv/bin/python ${path}/scripts/monitoring/auto_allocate_ecs_resources.py \
  --cluster-name "${cluster_name}" \
  --range-days "${range_days}" \
  --period-seconds "${period_seconds}"
