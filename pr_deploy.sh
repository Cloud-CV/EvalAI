#!/usr/bin/env bash
if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    echo "Not a Pull Request. Skipping surge deployment"
    exit 0
fi

npm i -g surge

export SURGE_LOGIN=$SURGE_LOGIN
export SURGE_TOKEN=$SURGE_TOKEN

export DEPLOY_DOMAIN=https://pr-${TRAVIS_PULL_REQUEST}-evalai.surge.sh
surge --project ./dist --domain $DEPLOY_DOMAIN;
