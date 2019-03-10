#!/usr/bin/env bash
if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    echo "Not a Pull Request. Skipping surge deployment"
    exit 0
fi
echo "PR Deploy routine START"
npm i -g surge

export SURGE_LOGIN=$SURGE_LOGIN
export SURGE_TOKEN=$SURGE_TOKEN

export DEPLOY_DOMAIN=https://pr-${TRAVIS_PULL_REQUEST}-evalai.surge.sh
echo $SURGE_LOGIN
echo $DEPLOY_DOMAIN

surge --project ./dist --domain $DEPLOY_DOMAIN;
