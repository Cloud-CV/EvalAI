if [ "$TRAVIS_PULL_REQUEST" != "false" -o "$TRAVIS_BRANCH" != "staging" -o "$TRAVIS_BRANCH" != "production" ]; then
    echo "Skipping deploy to staging or production server; The request or commit is not on staging or production branch"
    exit 0
fi

build_and_push() {

    if [ $2 == "false" -a $1 == "staging" -o $1 == "production"]; then

        # Set AWS default region
        aws configure set default.region us-east-1

        # Authenticate against our Docker registry
        eval $(aws ecr get-login --no-include-email)

        # Build and push the container images
        docker-compose -f docker-compose-$1.yml build
        docker-compose -f docker-compose-$1.yml push

    else
        echo "Skipping deploy to both Staging or Production Server"
        exit 0
    fi

}

build_and_push $TRAVIS_BRANCH, $TRAVIS_PULL_REQUEST
