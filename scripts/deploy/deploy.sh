#!/bin/bash
set -e

export AWS_ACCOUNT_ID=937891341272
export COMMIT_ID=$(git rev-parse HEAD)

build_and_push() {
        aws configure set default.region us-east-1
        eval $(aws ecr get-login --no-include-email)
        docker-compose -f docker-compose-$1.yml build
        docker-compose -f docker-compose-$1.yml push

        # Get the build docker images
        images=$(cat docker-compose-$1.yml | grep 'image: ' | cut -d':' -f 2 | tr -d '"')

        # It is used to tag & push the images with latest tag
        for image in $images
        do
            eval image=${image}
            docker tag ${image}:${COMMIT_ID} ${image}:latest
            docker push ${image}:latest
        done
}

build_and_push $1
