#!/bin/bash
path=$PWD
if [ ! -z "$1" ]
  then
    path=$1
fi
python ${path}/scripts/monitoring/monitor_containers.py
