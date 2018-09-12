#!/bin/bash
set -e

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
            docker tag "${image}":"$2" "${image}":"latest"
            docker push "${image}":"latest"
        done
}

if [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
    echo "Skipping deploy to staging or production server; The request or commit is not on staging or production branch"
    exit 0

elif [ "${TRAVIS_BRANCH}" == "staging" -o "${TRAVIS_BRANCH}" == "production" ]; then
    build_and_push $TRAVIS_BRANCH $TRAVIS_COMMIT
    exit 0

else
    echo "Skipping deploy!"
    exit 0
fi
