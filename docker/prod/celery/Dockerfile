ARG AWS_ACCOUNT_ID
ARG COMMIT_ID
ARG GITHUB_BRANCH_NAME

FROM ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-${GITHUB_BRANCH_NAME}-backend:${COMMIT_ID}

CMD ["sh", "/code/docker/prod/celery/container-start.sh"]
