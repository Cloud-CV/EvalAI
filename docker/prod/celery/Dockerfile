ARG AWS_ACCOUNT_ID
ARG COMMIT_ID
ARG TRAVIS_BRANCH

FROM ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-${TRAVIS_BRANCH}-backend:${COMMIT_ID}

CMD ["sh", "/code/docker/prod/celery/container-start.sh"]
