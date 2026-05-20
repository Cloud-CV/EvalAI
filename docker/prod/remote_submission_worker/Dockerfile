# syntax=docker/dockerfile:1
# Thin image: reuse the submission worker image built for worker_py3.7 so
# COMPOSE_BAKE does not compile docker/prod/worker_py3_7/Dockerfile twice in
# parallel (which produced empty site-packages on evalai-*-worker-py3.7).
ARG AWS_ACCOUNT_ID
ARG COMMIT_ID
ARG DEPLOYMENT_ENV
FROM ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-${DEPLOYMENT_ENV}-worker-py3.7:${COMMIT_ID}

CMD ["python", "-m", "scripts.workers.remote_submission_worker"]
