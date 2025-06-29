#!/usr/bin/env bash

# Check if this is a pull request
if [ "$GITHUB_EVENT_NAME" != "pull_request" ]; then
    echo "Not a Pull Request. Skipping surge deployment"
    exit 0
fi
echo "PR deployment start"
npm i -g surge
echo "Installed surge successfully"

# Use GitHub's pull request number from the event payload
export DEPLOY_DOMAIN=https://pr-${GITHUB_PR_NUMBER}-evalai.surge.sh
echo "Deployment domain:"
echo $DEPLOY_DOMAIN

surge --project ./dist --domain $DEPLOY_DOMAIN --token $SURGE_TOKEN
