#!/bin/bash
set -euo pipefail

operation_name="${1:-}"
target_environment="${2:-${DEPLOYMENT_BRANCH_NAME:-${GITHUB_REF_NAME:-}}}"
dry_run_deployment="${DRY_RUN_DEPLOYMENT:-false}"
aws_region="${AWS_REGION:-us-east-1}"

if [[ -z "${COMMIT_ID:-}" ]]; then
    export COMMIT_ID="latest"
fi

require_variable() {
    local variable_name="$1"
    if [[ -z "${!variable_name:-}" ]]; then
        echo "Required environment variable '${variable_name}' is not set."
        exit 1
    fi
}

validate_target_environment() {
    if [[ -z "${target_environment}" ]]; then
        echo "Target environment is required. Provide it as the second argument or set DEPLOYMENT_BRANCH_NAME."
        exit 1
    fi

    if [[ "${target_environment}" != "staging" && "${target_environment}" != "production" ]]; then
        echo "Skipping deployment since target environment '${target_environment}' is not staging or production."
        exit 0
    fi
}

resolve_deployment_instance_host() {
    if [[ -n "${TARGET_INSTANCE_HOST:-}" ]]; then
        echo "${TARGET_INSTANCE_HOST}"
        return
    fi

    case "${target_environment}" in
        production)
            require_variable PRODUCTION_INSTANCE
            echo "${PRODUCTION_INSTANCE}"
            ;;
        staging)
            require_variable STAGING_INSTANCE
            echo "${STAGING_INSTANCE}"
            ;;
        *)
            echo ""
            ;;
    esac
}

aws_login() {
    require_variable AWS_ACCOUNT_ID
    aws configure set default.region "${aws_region}"
    aws ecr get-login-password --region "${aws_region}" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${aws_region}.amazonaws.com"
}

get_evalai_api_base_url() {
    if [[ "${target_environment}" == "staging" ]]; then
        echo "https://staging.eval.ai"
    else
        echo "https://eval.ai"
    fi
}

fetch_challenge_queue_name() {
    local api_authentication_token="$1"
    local challenge_primary_key="$2"
    local evalai_api_base_url
    evalai_api_base_url="$(get_evalai_api_base_url)"

    curl --fail --silent --show-error --location \
        -H "Authorization: Token ${api_authentication_token}" \
        "${evalai_api_base_url}/api/challenges/get_broker_url/${challenge_primary_key}/"
}

fetch_all_challenge_queue_names() {
    local api_authentication_token="$1"
    local evalai_api_base_url
    evalai_api_base_url="$(get_evalai_api_base_url)"

    curl --fail --silent --show-error --location \
        -H "Authorization: Token ${api_authentication_token}" \
        "${evalai_api_base_url}/api/challenges/get_broker_urls/"
}

perform_auto_deploy() {
    validate_target_environment
    require_variable AWS_ACCOUNT_ID
    require_variable JUMPBOX_INSTANCE

    local deployment_instance_host
    deployment_instance_host="$(resolve_deployment_instance_host)"
    if [[ -z "${deployment_instance_host}" ]]; then
        echo "Deployment target host is empty. Set TARGET_INSTANCE_HOST or STAGING_INSTANCE / PRODUCTION_INSTANCE for '${target_environment}'."
        exit 1
    fi
    local ssh_private_key_path="${SSH_PRIVATE_KEY_PATH:-scripts/deployment/evalai.pem}"
    local deploy_ssh_known_hosts_path="${DEPLOY_SSH_KNOWN_HOSTS_PATH:-$HOME/.ssh/known_hosts}"

    if [[ ! -f "${ssh_private_key_path}" ]]; then
        echo "SSH private key file not found at '${ssh_private_key_path}'."
        exit 1
    fi

    if [[ ! -f "${deploy_ssh_known_hosts_path}" ]]; then
        echo "Known hosts file not found at '${deploy_ssh_known_hosts_path}'."
        echo "Set DEPLOY_SSH_KNOWN_HOSTS_PATH to a valid known_hosts file."
        exit 1
    fi

    chmod 600 "${ssh_private_key_path}"

    ssh \
        -i "${ssh_private_key_path}" \
        -o BatchMode=yes \
        -o IdentitiesOnly=yes \
        -o StrictHostKeyChecking=yes \
        -o UserKnownHostsFile="${deploy_ssh_known_hosts_path}" \
        -o ProxyJump="ubuntu@${JUMPBOX_INSTANCE}" \
        "ubuntu@${deployment_instance_host}" <<ENDSSH
set -euo pipefail

cd ~/Projects/EvalAI
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
export COMMIT_ID="${COMMIT_ID}"
export AWS_DEFAULT_REGION="${aws_region}"
export TARGET_ENVIRONMENT="${target_environment}"
export DRY_RUN_DEPLOYMENT="${dry_run_deployment}"

aws ecr get-login-password --region "\${AWS_DEFAULT_REGION}" | docker login --username AWS --password-stdin "\${AWS_ACCOUNT_ID}.dkr.ecr.\${AWS_DEFAULT_REGION}.amazonaws.com"
aws s3 cp "s3://cloudcv-secrets/evalai/\${TARGET_ENVIRONMENT}/docker_\${TARGET_ENVIRONMENT}.env" "./docker/prod/docker_\${TARGET_ENVIRONMENT}.env"

if [[ "\${DRY_RUN_DEPLOYMENT}" == "true" ]]; then
    echo "Dry-run mode enabled. Validating Docker Compose configuration only."
    docker compose -f "docker-compose-\${TARGET_ENVIRONMENT}.yml" config >/dev/null
    exit 0
fi

docker compose -f "docker-compose-\${TARGET_ENVIRONMENT}.yml" pull django nodejs celery memcached
docker compose -f "docker-compose-\${TARGET_ENVIRONMENT}.yml" up -d --force-recreate --remove-orphans django nodejs celery memcached
ENDSSH
}

case "${operation_name}" in
    auto_deploy)
        perform_auto_deploy
        ;;
    pull)
        validate_target_environment
        aws_login
        echo "Pulling environment variables file..."
        aws s3 cp \
            "s3://cloudcv-secrets/evalai/${target_environment}/docker_${target_environment}.env" \
            "./docker/prod/docker_${target_environment}.env"
        echo "Environment variables file downloaded successfully."
        echo "Pulling docker images from ECR..."
        docker compose -f "docker-compose-${target_environment}.yml" pull
        echo "Completed pull operation."
        ;;
    deploy-django)
        validate_target_environment
        echo "Deploying django docker container..."
        docker compose -f "docker-compose-${target_environment}.yml" up -d django
        echo "Completed deploy operation."
        ;;
    deploy-nodejs)
        validate_target_environment
        echo "Deploying nodejs docker container..."
        docker compose -f "docker-compose-${target_environment}.yml" up -d nodejs
        echo "Completed deploy operation."
        ;;
    deploy-nodejs-v2)
        validate_target_environment
        echo "Deploying new frontend docker container..."
        docker compose -f "docker-compose-${target_environment}.yml" up -d nodejs_v2
        echo "Completed deploy operation."
        ;;
    deploy-celery)
        validate_target_environment
        echo "Deploying celery docker container..."
        docker compose -f "docker-compose-${target_environment}.yml" up -d celery
        echo "Completed deploy operation."
        ;;
    deploy-worker)
        validate_target_environment
        api_authentication_token="${3:-}"
        challenge_primary_key="${4:-}"
        if [[ -z "${challenge_primary_key}" ]]; then
            echo "Please provide the challenge ID."
            exit 1
        fi
        if [[ -z "${api_authentication_token}" ]]; then
            echo "Please provide the API authentication token."
            exit 1
        fi
        echo "Fetching queue name for challenge ${challenge_primary_key} on ${target_environment}..."
        queue_name_response="$(fetch_challenge_queue_name "${api_authentication_token}" "${challenge_primary_key}")"
        queue_name_array=($(echo "${queue_name_response//,/ }" | tr -d '[]'))
        challenge_queue_name="$(echo "${queue_name_array}" | tr -d '"')"
        echo "Deploying worker for queue: ${challenge_queue_name}"
        docker compose -f "docker-compose-${target_environment}.yml" run \
            --name="worker_${challenge_queue_name}" \
            -e "CHALLENGE_QUEUE=${challenge_queue_name}" \
            -e "CHALLENGE_PK=${challenge_primary_key}" \
            -d worker
        echo "Deployed worker docker container for queue: ${challenge_queue_name}"
        ;;
    deploy-worker-py3-8)
        validate_target_environment
        api_authentication_token="${3:-}"
        challenge_primary_key="${4:-}"
        if [[ -z "${challenge_primary_key}" ]]; then
            echo "Please provide the challenge ID."
            exit 1
        fi
        if [[ -z "${api_authentication_token}" ]]; then
            echo "Please provide the API authentication token."
            exit 1
        fi
        echo "Fetching queue name for challenge ${challenge_primary_key} on ${target_environment}..."
        queue_name_response="$(fetch_challenge_queue_name "${api_authentication_token}" "${challenge_primary_key}")"
        queue_name_array=($(echo "${queue_name_response//,/ }" | tr -d '[]'))
        challenge_queue_name="$(echo "${queue_name_array}" | tr -d '"')"
        echo "Deploying worker_py3_8 for queue: ${challenge_queue_name}"
        docker compose -f "docker-compose-${target_environment}.yml" run \
            --name="worker_${challenge_queue_name}" \
            -e "CHALLENGE_QUEUE=${challenge_queue_name}" \
            -e "CHALLENGE_PK=${challenge_primary_key}" \
            -d worker_py3_8
        echo "Deployed worker_py3_8 docker container for queue: ${challenge_queue_name}"
        ;;
    deploy-remote-worker)
        validate_target_environment
        api_authentication_token="${3:-}"
        remote_queue_name="${4:-}"
        if [[ -z "${api_authentication_token}" ]]; then
            echo "Please provide the auth token."
            exit 1
        fi
        if [[ -z "${remote_queue_name}" ]]; then
            echo "Please provide the queue name."
            exit 1
        fi
        echo "Deploying remote worker for queue: ${remote_queue_name}"
        docker compose -f "docker-compose-${target_environment}.yml" run \
            --name="remote_worker_${remote_queue_name}" \
            -e "QUEUE_NAME=${remote_queue_name}" \
            -e "AUTH_TOKEN=${api_authentication_token}" \
            -d worker
        echo "Deployed remote worker container for queue: ${remote_queue_name}"
        ;;
    deploy-workers)
        validate_target_environment
        api_authentication_token="${3:-}"
        if [[ -z "${api_authentication_token}" ]]; then
            echo "Please provide the API authentication token."
            exit 1
        fi
        echo "Pulling queue names for ${target_environment} challenges..."
        queue_names_response="$(fetch_all_challenge_queue_names "${api_authentication_token}")"
        queue_names_array=($(echo "${queue_names_response//,/ }" | tr -d '[]'))
        for queue_name in "${queue_names_array[@]}"; do
            challenge_queue_name="$(echo "${queue_name}" | tr -d '"')"
            echo "Deploying worker for queue: ${challenge_queue_name}"
            docker compose -f "docker-compose-${target_environment}.yml" run \
                --name="worker_${challenge_queue_name}" \
                -e "CHALLENGE_QUEUE=${challenge_queue_name}" \
                -d worker
            echo "Deployed worker docker container for queue: ${challenge_queue_name}"
        done
        ;;
    scale)
        validate_target_environment
        service_name="${3:-}"
        instance_count="${4:-}"
        if [[ -z "${service_name}" || -z "${instance_count}" ]]; then
            echo "Please provide both service name and instance count."
            exit 1
        fi
        echo "Scaling the containers..."
        docker compose -f "docker-compose-${target_environment}.yml" \
            up -d --scale "${service_name}=${instance_count}" "${service_name}"
        ;;
    clean)
        validate_target_environment
        {
            docker compose -f "docker-compose-${target_environment}.yml" rm -s -v -f
        } || {
            echo "Delete operation skipped since no container or image was found."
        }
        existing_image_ids="$(docker images -a -q)"
        if [[ -n "${existing_image_ids}" ]]; then
            docker rmi ${existing_image_ids}
            echo "Successfully cleaned all Docker images."
        else
            echo "No Docker images found to remove."
        fi
        ;;
    *)
        echo "EvalAI deployment utility script"
        echo "Usage: $0 {auto_deploy|pull|deploy-django|deploy-nodejs|deploy-nodejs-v2|deploy-celery|deploy-worker|deploy-worker-py3-8|deploy-remote-worker|deploy-workers|scale|clean} [environment]"
        echo
        echo "Examples:"
        echo "  ./scripts/deployment/deploy.sh auto_deploy"
        echo "  ./scripts/deployment/deploy.sh pull production"
        echo "  ./scripts/deployment/deploy.sh deploy-django production"
        echo "  ./scripts/deployment/deploy.sh deploy-nodejs production"
        echo "  ./scripts/deployment/deploy.sh deploy-celery production"
        echo "  ./scripts/deployment/deploy.sh deploy-worker production <superuser_auth_token> <challenge_pk>"
        echo "  ./scripts/deployment/deploy.sh deploy-worker-py3-8 production <superuser_auth_token> <challenge_pk>"
        echo "  ./scripts/deployment/deploy.sh deploy-remote-worker production <auth_token> <queue_name>"
        echo "  ./scripts/deployment/deploy.sh deploy-workers production <superuser_auth_token>"
        echo "  ./scripts/deployment/deploy.sh scale production django 5"
        echo "  ./scripts/deployment/deploy.sh clean production"
        exit 1
        ;;
esac
