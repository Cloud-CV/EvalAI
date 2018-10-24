#!/bin/bash
set -e

export COMMIT_ID=$(git rev-parse HEAD)

build_and_push() {
        aws configure set default.region us-east-1
        eval $(aws ecr get-login --no-include-email)
        docker-compose -f docker-compose-$1.yml build
        docker-compose -f docker-compose-$1.yml push

        # Get already built docker images
        images=$(cat docker-compose-$1.yml | grep 'image: ' | cut -d':' -f 2 | tr -d '"')

        # Tag & push images with latest tag
        for image in $images
        do
            eval image=${image}
            docker tag ${image}:${COMMIT_ID} ${image}:latest
            docker push ${image}:latest
        done
}

build_and_push $1
