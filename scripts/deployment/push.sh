#!/bin/bash
set -euo pipefail

export COMMIT_ID="${COMMIT_ID:-$(git rev-parse HEAD)}"

deployment_branch_name="${DEPLOYMENT_BRANCH_NAME:-${GITHUB_REF_NAME:-}}"
continuous_integration_event_name="${CI_EVENT_NAME:-${GITHUB_EVENT_NAME:-manual}}"
is_pull_request_build="${IS_PULL_REQUEST_BUILD:-false}"
dry_run_deployment="${DRY_RUN_DEPLOYMENT:-false}"
aws_region="${AWS_REGION:-us-east-1}"

require_variable() {
    local variable_name="$1"
    if [[ -z "${!variable_name:-}" ]]; then
        echo "Required environment variable '${variable_name}' is not set."
        exit 1
    fi
}

verify_submission_worker_images() {
    local deployment_environment_name="$1"
    local -a worker_ecr_repositories=(
        "evalai-${deployment_environment_name}-worker-py3.7"
        "evalai-${deployment_environment_name}-worker-py3.8"
        "evalai-${deployment_environment_name}-worker-py3.9"
    )

    for worker_ecr_repository in "${worker_ecr_repositories[@]}"; do
        local worker_image="${AWS_ACCOUNT_ID}.dkr.ecr.${aws_region}.amazonaws.com/${worker_ecr_repository}:${COMMIT_ID}"
        echo "Verifying Python dependencies in ${worker_image}..."
        docker run --rm "${worker_image}" python -c "import boto3, django; print('OK', boto3.__version__, django.get_version())"
    done
}

build_and_push_images() {
    local deployment_environment_name="$1"
    local compose_file_path="docker-compose-${deployment_environment_name}.yml"
    local deploy_cache_compose_path="docker/docker-compose.deploy-cache.yml"

    aws configure set default.region "${aws_region}"
    aws ecr get-login-password --region "${aws_region}" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${aws_region}.amazonaws.com"

    echo "Pulling SSL certificates and nginx configuration..."
    aws s3 cp s3://cloudcv-secrets/eval.ai/ssl/ ./ssl/ --recursive
    aws s3 cp s3://cloudcv-secrets/ssl/ ./ssl/ --recursive
    aws s3 cp \
        "s3://cloudcv-secrets/evalai/${deployment_environment_name}/nginx_${deployment_environment_name}.conf" \
        "./docker/prod/nodejs/nginx_${deployment_environment_name}.conf"
    echo "Pulled SSL certificates and nginx configuration successfully."

    if [[ "${dry_run_deployment}" == "true" ]]; then
        echo "Dry-run mode enabled. Validating Docker Compose configuration only."
        docker compose -f "${compose_file_path}" config >/dev/null
        return 0
    fi

    local -a compose_file_arguments=(-f "${compose_file_path}")
    if [[ -f "${deploy_cache_compose_path}" ]]; then
        compose_file_arguments+=(-f "${deploy_cache_compose_path}")
    fi

    local -a shared_build_arguments=(
        "${compose_file_arguments[@]}"
        build
        --build-arg "COMMIT_ID=${COMMIT_ID}"
        --build-arg "EVALAI_GIT_REVISION=${COMMIT_ID}"
        --build-arg "AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}"
        --compress
    )

    # Bake parallelizes services that share docker/prod/worker_py3_7/Dockerfile and
    # produced images with empty site-packages. Build workers sequentially first.
    unset COMPOSE_BAKE

    echo "=== Building submission worker images (worker_py3_7 without cache) ==="
    DOCKER_BUILDKIT=1 docker compose "${shared_build_arguments[@]}" --no-cache worker_py3_7
    DOCKER_BUILDKIT=1 docker compose "${shared_build_arguments[@]}" worker_py3_8 worker_py3_9

    verify_submission_worker_images "${deployment_environment_name}"

    echo "=== Building remaining deploy images (remote-worker reuses worker_py3.7 image) ==="
    DOCKER_BUILDKIT=1 docker compose "${shared_build_arguments[@]}" \
        django celery nodejs remote-worker code-upload-worker

    echo "=== Pushing commit-tagged images to ECR ==="
    docker compose "${compose_file_arguments[@]}" push

    echo "=== Tagging and pushing :latest after worker verification ==="
    local container_image_references
    container_image_references=$(
        docker compose -f "${compose_file_path}" config | \
            awk '/image:/ {print $2}' | \
            grep "${AWS_ACCOUNT_ID}.dkr.ecr.${aws_region}.amazonaws.com/evalai-" | \
            sort -u || true
    )

    while IFS= read -r container_image_reference; do
        [[ -z "${container_image_reference}" ]] && continue
        local container_image_repository="${container_image_reference%%:*}"
        docker tag "${container_image_repository}:${COMMIT_ID}" "${container_image_repository}:latest"
        docker push "${container_image_repository}:latest"
    done <<< "${container_image_references}"
}

require_variable AWS_ACCOUNT_ID

if [[ -z "${deployment_branch_name}" ]]; then
    echo "DEPLOYMENT_BRANCH_NAME or GITHUB_REF_NAME must be set before running push.sh."
    exit 1
fi

if [[ "${continuous_integration_event_name}" == "pull_request" || "${is_pull_request_build}" == "true" ]]; then
    echo "Skipping image push for pull request builds."
    exit 0
fi

if [[ "${deployment_branch_name}" == "staging" || "${deployment_branch_name}" == "production" ]]; then
    build_and_push_images "${deployment_branch_name}"
    exit 0
fi

echo "Skipping deploy image push because branch '${deployment_branch_name}' is not staging or production."
exit 0
