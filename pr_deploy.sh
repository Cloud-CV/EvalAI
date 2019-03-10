#!/usr/bin/env bash
if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    echo "Not a Pull Request. Skipping surge deployment"
    exit 0
fi
echo "PR deployment start"
npm i -g surge
echo "Installed surge successfully"
export DEPLOY_DOMAIN=https://pr-${TRAVIS_PULL_REQUEST}-evalai.surge.sh
echo "Deployment domain -"
echo $DEPLOY_DOMAIN

surge --project ./dist --domain $DEPLOY_DOMAIN --token $SURGE_TOKEN
