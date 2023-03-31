#!/bin/bash
path=$PWD
api_host_url=''
eks_aws_storage_bucket_name=''

if [ ! -z "$1" ]
  then
    path=$1
fi

if [ ! -z "$2" ]
  then
    api_host_url=$2
fi

if [ ! -z "$3" ]
  then
    monitoring_api_url=$3
fi

if [ ! -z "$4" ]
  then
    env=$4
fi

if [ ! -z "$5" ]
  then
    eks_aws_account_id=$5
fi

if [ ! -z "$6" ]
  then
    eks_aws_access_key_id=$6
fi

if [ ! -z "$7" ]
  then
    eks_aws_secret_access_key=$7
fi

if [ ! -z "$8" ]
  then
    eks_aws_region=$8
fi

if [ ! -z "$9" ]
  then
    eks_aws_storage_bucket_name=$9
fi

# crontab doesn't have access to env variable, define explicitly
export API_HOST_URL=${api_host_url};
export MONITORING_API_URL=${monitoring_api_url};
export ENV=${env}
export EKS_AWS_ACCOUNT_ID=${eks_aws_account_id}
export EKS_AWS_ACCESS_KEY_ID=${eks_aws_access_key_id}
export EKS_AWS_SECRET_ACCESS_KEY=${eks_aws_secret_access_key}
export EKS_AWS_REGION=${eks_aws_region}
export EKS_AWS_STORAGE_BUCKET_NAME=${eks_aws_storage_bucket_name}

/home/ubuntu/venv/bin/python ${path}/scripts/monitoring/auto_scale_eks_nodes.py
