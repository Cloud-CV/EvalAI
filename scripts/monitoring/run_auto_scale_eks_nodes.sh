#!/bin/bash
path=$PWD
auth_token=''
json_path=''
api_host_url=''
eks_aws_storage_bucket_name=''

if [ ! -z "$1" ]; then
  path=$1
fi

if [ ! -z "$2" ]; then
    auth_token=$2
fi

if [ ! -z "$3" ]; then
  json_path=$3
fi

if [ ! -z "$4" ]; then
  api_host_url=$4
fi

if [ ! -z "$5" ]; then
  env=$5
fi

if [ ! -z "$6" ]; then
  eks_aws_account_id=$6
fi

if [ ! -z "$7" ]; then
  eks_aws_access_key_id=$7
fi

if [ ! -z "$8" ]; then
  eks_aws_secret_access_key=$8
fi

if [ ! -z "$9" ]; then
  eks_aws_region=$9
fi

if [ ! -z "${10}" ]; then
  eks_aws_storage_bucket_name=${10}
fi

# crontab doesn't have access to env variable, define explicitly
export AUTH_TOKEN=${auth_token};
export JSON_PATH=${json_path}
export API_HOST_URL=${api_host_url}
export ENV=${env}
export EKS_AWS_ACCOUNT_ID=${eks_aws_account_id}
export EKS_AWS_ACCESS_KEY_ID=${eks_aws_access_key_id}
export EKS_AWS_SECRET_ACCESS_KEY=${eks_aws_secret_access_key}
export EKS_AWS_REGION=${eks_aws_region}
export EKS_AWS_STORAGE_BUCKET_NAME=${eks_aws_storage_bucket_name}

/home/ubuntu/venv/bin/python ${path}/scripts/monitoring/auto_scale_eks_nodes.py
