#!/bin/sh
# Usage:
# bash rl_worker_kube_warmup.sh [FLAGS]
#
# Environment Variables to be passed:
# CLUSTER_NAME: Name of EKS Cluster
#
# Flags:
# new-config: To overwrite kube config. Can also be used if kube config is not present

RED='\033[0;31m'
NC='\033[0m'
KUBE_CONFIG_PATH=$HOME/.kube/config

if [[ ! -f "$KUBE_CONFIG_PATH" ]] || [[ $* == --new-config ]]; then
    if [[ -z "${CLUSTER_NAME}" ]]; then
        echo -e "${RED}ERROR: CLUSTER_NAME variable not set!${NC}"
        exit 1
    fi
    aws eks update-kubeconfig --name $CLUSTER_NAME
fi
