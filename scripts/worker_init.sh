#!/bin/bash

if [ $# -gt 0 ]
  then
    file_url=$1
    output_file = "/code/requirements/worker/custom_requirements.txt"
    curl $file_url > $output_file
    pip install -r $output_file

python -m "scripts.workers.submission_worker.py"