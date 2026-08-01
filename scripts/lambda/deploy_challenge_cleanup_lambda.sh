#!/usr/bin/env bash
#
# Deploy the challenge cleanup Lambda and its supporting AWS configuration.
#
# Mirrors deploy_auto_scale_eks_nodes_lambda.sh: single source of truth for
# this function's code and configuration instead of manual console edits.
#
# Usage:
#   ENVIRONMENT=production \
#   ECS_CLUSTER=evalai-prod-cluster \
#   EVALAI_API_SERVER=https://eval.ai \
#   LAMBDA_AUTH_TOKEN=xxx \
#   EVENTBRIDGE_SCHEDULER_ROLE_ARN=arn:aws:iam::123456789012:role/evalai-scheduler \
#   ./scripts/lambda/deploy_challenge_cleanup_lambda.sh
#
# Optional:
#   AWS_REGION                (default us-east-1)
#   AWS_PROFILE                passed through to the AWS CLI
#   FUNCTION_NAME               override the derived function name
#   CLEANUP_RETRY_DELAY_MINUTES  minutes between pending-submission re-checks
#                                (default 60, matches the Lambda's own default)
#   DLQ_ARN                    SQS queue / SNS topic ARN for failed async invocations
#   SKIP_CONFIG=1              skip updating function configuration/env vars

set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT is required (e.g. production, staging)}"
AWS_REGION="${AWS_REGION:-us-east-1}"

FUNCTION_NAME="${FUNCTION_NAME:-evalai-${ENVIRONMENT}-challenge-cleanup}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(mktemp -d)"
ZIP_PATH="${BUILD_DIR}/challenge_cleanup_lambda.zip"

trap 'rm -rf "${BUILD_DIR}"' EXIT

aws_cli() {
    if [ -n "${AWS_PROFILE:-}" ]; then
        aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" "$@"
    else
        aws --region "${AWS_REGION}" "$@"
    fi
}

echo "==> Packaging ${FUNCTION_NAME}"
cp "${SCRIPT_DIR}/challenge_cleanup_lambda.py" "${BUILD_DIR}/"
(cd "${BUILD_DIR}" && zip -q "${ZIP_PATH}" challenge_cleanup_lambda.py)

echo "==> Updating function code"
aws_cli lambda update-function-code \
    --function-name "${FUNCTION_NAME}" \
    --zip-file "fileb://${ZIP_PATH}" \
    --publish >/dev/null

aws_cli lambda wait function-updated \
    --function-name "${FUNCTION_NAME}"

if [ "${SKIP_CONFIG:-0}" = "1" ]; then
    echo "==> Skipping configuration update (SKIP_CONFIG=1)"
    exit 0
fi

if [ -z "${ECS_CLUSTER:-}" ] || [ -z "${EVALAI_API_SERVER:-}" ] \
    || [ -z "${LAMBDA_AUTH_TOKEN:-}" ] \
    || [ -z "${EVENTBRIDGE_SCHEDULER_ROLE_ARN:-}" ]; then
    echo "==> Skipping configuration update" \
         "(set ECS_CLUSTER, EVALAI_API_SERVER, LAMBDA_AUTH_TOKEN," \
         "and EVENTBRIDGE_SCHEDULER_ROLE_ARN to apply)"
    exit 0
fi

echo "==> Resolving function ARN (needed for self-rescheduling)"
FUNCTION_ARN="$(aws_cli lambda get-function \
    --function-name "${FUNCTION_NAME}" \
    --query "Configuration.FunctionArn" --output text)"

echo "==> Updating function configuration"
ENV_VARS="ECS_CLUSTER=${ECS_CLUSTER}"
ENV_VARS="${ENV_VARS},ENVIRONMENT=${ENVIRONMENT}"
ENV_VARS="${ENV_VARS},EVALAI_API_SERVER=${EVALAI_API_SERVER}"
ENV_VARS="${ENV_VARS},LAMBDA_AUTH_TOKEN=${LAMBDA_AUTH_TOKEN}"
ENV_VARS="${ENV_VARS},EVENTBRIDGE_SCHEDULER_ROLE_ARN=${EVENTBRIDGE_SCHEDULER_ROLE_ARN}"
ENV_VARS="${ENV_VARS},CHALLENGE_CLEANUP_LAMBDA_ARN=${FUNCTION_ARN}"
if [ -n "${CLEANUP_RETRY_DELAY_MINUTES:-}" ]; then
    ENV_VARS="${ENV_VARS},CLEANUP_RETRY_DELAY_MINUTES=${CLEANUP_RETRY_DELAY_MINUTES}"
fi

CONFIG_ARGS=(
    --function-name "${FUNCTION_NAME}"
    --environment "Variables={${ENV_VARS}}"
    --timeout 300
)
# Cleanup is invoked by EventBridge Scheduler; routing failures to a DLQ is
# what makes a dropped/erroring invocation visible instead of silently lost.
if [ -n "${DLQ_ARN:-}" ]; then
    CONFIG_ARGS+=(--dead-letter-config "TargetArn=${DLQ_ARN}")
fi

aws_cli lambda update-function-configuration "${CONFIG_ARGS[@]}" >/dev/null
aws_cli lambda wait function-updated --function-name "${FUNCTION_NAME}"

echo "==> Done: ${FUNCTION_NAME}"
