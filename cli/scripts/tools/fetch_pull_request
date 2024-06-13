#!/bin/bash
if [ "$1" == "--help" ]; then
    printf "Usage: fetch-pull-request [--help] pull_request_id [remote=origin] \n\n Locally fetch a pull request and test it. \n Remote is set to origin by default.\n"
    exit 1
elif [ $# -eq 0 ]; then
    echo "Pull request id not given."
    exit 1
else
    set -e -x
    remote=${2:-origin}
    git branch -D review-$1 || git fetch $remote pull/$1/head:review-$1
    git checkout review-$1
fi
