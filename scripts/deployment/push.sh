#!/bin/bash
set -e

export COMMIT_ID=$(git rev-parse HEAD)

build_and_push() {
        aws configure set default.region us-east-1
        eval $(aws ecr get-login --no-include-email)
        echo "Pulling ssl certificates and nginx configuration..."
        aws s3 cp s3://cloudcv-secrets/eval.ai/ssl/ ./ssl/ --recursive
        # Need ssl files related to *.cloudcv.org since we want to provide backward compatibility
        aws s3 cp s3://cloudcv-secrets/evalai/${TRAVIS_BRANCH}/ssl/ ./ssl/ --recursive
        echo "Pulled ssl certificates and nginx configuration successfully"
        docker-compose -f docker-compose-$1.yml build \
            --build-arg COMMIT_ID=${COMMIT_ID} \
            --build-arg TRAVIS_BRANCH=${TRAVIS_BRANCH} \
            --build-arg AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID} --compress
        docker-compose -f docker-compose-$1.yml push

        # Get already built docker images
        images=$(cat docker-compose-$1.yml | grep 'image: ${AWS_ACCOUNT_ID' | cut -d':' -f 2 | tr -d '"')

        # Tag & push images with latest tag
        for image in $images
        do
            eval image=${image}
            docker tag ${image}:${COMMIT_ID} ${image}:latest
            docker push ${image}:latest
        done
}

if [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
    echo "Skipping deploy to staging or production server; The request or commit is not on staging or production branch"
    exit 0
elif [ "${TRAVIS_BRANCH}" == "staging" -o "${TRAVIS_BRANCH}" == "production" ]; then
    build_and_push $TRAVIS_BRANCH
    exit 0
else
    echo "Skipping deploy!"
    exit 0
fi
