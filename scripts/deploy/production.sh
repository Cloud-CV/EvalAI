BRANCH="production"
SHA=`git rev-parse --verify HEAD`

if [ "$TRAVIS_PULL_REQUEST" != "false" -o "$TRAVIS_BRANCH" != "$BRANCH" ]; then
    echo "Skipping deploy to production server; The request or commit is not on production branch"
    exit 0
fi

# Set AWS default region
aws configure set default.region us-east-1

# Authenticate against our Docker registry
eval $(aws ecr get-login --no-include-email)

# Build and push the Django container image
docker-compose -f docker-compose-prod.yml build
docker-compose -f docker-compose-prod.yml push
