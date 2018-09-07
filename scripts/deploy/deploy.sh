if [ "$TRAVIS_PULL_REQUEST" != "false" -o "$TRAVIS_BRANCH" != "staging" -o "$TRAVIS_BRANCH" != "production" ]; then
    echo "Skipping deploy to staging or production server; The request or commit is not on staging or production branch"
    exit 0
fi

if [ "$TRAVIS_PULL_REQUEST" != "false" -a "TRAVIS_BRANCH" != "staging"]; then

    # Set AWS default region
    aws configure set default.region us-east-1

    # Authenticate against our Docker registry
    eval $(aws ecr get-login --no-include-email)

    # Build and push the container images
    docker-compose -f docker-compose-staging.yml build
    docker-compose -f docker-compose-staging.yml push
    exit 0

elif [ "$TRAVIS_PULL_REQUEST" != "false" -a "TRAVIS_BRANCH" != "production"]; then

    # Set AWS default region
    aws configure set default.region us-east-1

    # Authenticate against our Docker registry
    eval $(aws ecr get-login --no-include-email)

    # Build and push the container images
    docker-compose -f docker-compose-prod.yml build
    docker-compose -f docker-compose-prod.yml push
    exit 0

else
    echo "Skipping deploy to both Staging or Production Server"
    exit 0
fi
