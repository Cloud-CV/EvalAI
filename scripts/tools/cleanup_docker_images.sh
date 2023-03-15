#!/bin/bash

if [[ "$1" == "production" ]]; then
  env_filter='*/evalai-production*:*'
else
  env_filter='*/evalai-staging*:*'
fi

# Remove all dangling (with <none> tag)
docker images --filter='dangling=true' --format='{{.ID}}' | xargs -r docker rmi

# Remove all with `env_filter` but without `latest` tag
docker images --filter=reference='*/*:latest'|awk '{print $3}' > latest_tagged_images.txt
docker images --filter=reference=$env_filter|awk '{print $3'} > all_images.txt
docker rmi -f $(grep -v -f latest_tagged_images.txt all_images.txt)

# Cleanup the temporary files
# rm all_images.txt latest_tagged_images.txt