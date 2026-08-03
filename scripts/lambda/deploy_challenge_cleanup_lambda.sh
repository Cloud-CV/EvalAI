#!/usr/bin/env bash
#
# Deploy the challenge cleanup Lambda and its supporting AWS configuration.
#
# Mirrors deploy_auto_scale_eks_nodes_lambda.sh: single source of truth for
# this function's code and configuration instead of manual console edits.
#
# Only the code is updated unconditionally. Configuration is fetched from
# the live function first and merged with whatever env vars you pass here,
# so you only need to supply values you're changing - anything already set
# on the function (including vars this script doesn't know about) is left
# alone. On a function's first deploy, nothing is set yet, so pass every
# required var at least once. Configuration is validated before any code
# is published, so a misconfigured first deploy fails without leaving a
# new Lambda version live with incomplete config.
#
# Usage:
#   ENVIRONMENT=production \
#   ECS_CLUSTER=evalai-prod-cluster \
#   EVALAI_API_SERVER=https://eval.ai \
#   LAMBDA_AUTH_TOKEN=xxx \
#   EVENTBRIDGE_SCHEDULER_ROLE_ARN=arn:aws:iam::123456789012:role/evalai-scheduler \
#   ./scripts/lambda/deploy_challenge_cleanup_lambda.sh
#
# Optional (only overrides the existing value on the function if set):
#   AWS_REGION                    (falls back to us-east-1 if nothing is set)
#   ECS_CLUSTER, EVALAI_API_SERVER, LAMBDA_AUTH_TOKEN,
#   EVENTBRIDGE_SCHEDULER_ROLE_ARN, CLEANUP_RETRY_DELAY_MINUTES
#   AWS_PROFILE                    passed through to the AWS CLI
#   FUNCTION_NAME                  override the derived function name
#   DLQ_ARN                        SQS queue / SNS topic ARN for failed async invocations
#   SKIP_CONFIG=1                  skip validating/updating function configuration entirely
#
# Requires: aws CLI, jq

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

ENV_FILE=""

if [ "${SKIP_CONFIG:-0}" = "1" ]; then
    echo "==> Skipping configuration validation/update (SKIP_CONFIG=1)"
else
    echo "==> Fetching existing function configuration"
    EXISTING_ENV_JSON="$(aws_cli lambda get-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --query "Environment.Variables" --output json)"
    if [ "${EXISTING_ENV_JSON}" = "null" ]; then
        EXISTING_ENV_JSON="{}"
    fi

    echo "==> Resolving function ARN (needed for self-rescheduling)"
    FUNCTION_ARN="$(aws_cli lambda get-function \
        --function-name "${FUNCTION_NAME}" \
        --query "Configuration.FunctionArn" --output text)"

    # Only vars actually provided (plus the two always intrinsic to this
    # deploy) become overrides - anything else already on the function,
    # including vars this script doesn't know about, is left untouched.
    OVERRIDES_JSON="{}"
    set_override() {
        # Pass the value through an env var, not --arg, so secrets like
        # LAMBDA_AUTH_TOKEN never appear in this process's argv (visible
        # via `ps` to other users on the box).
        OVERRIDES_JSON="$(OVERRIDE_VALUE="$2" jq --arg k "$1" \
            '. + {($k): env.OVERRIDE_VALUE}' \
            <<<"${OVERRIDES_JSON}")"
    }
    if [ -n "${ECS_CLUSTER:-}" ]; then
        set_override ECS_CLUSTER "${ECS_CLUSTER}"
    fi
    if [ -n "${EVALAI_API_SERVER:-}" ]; then
        set_override EVALAI_API_SERVER "${EVALAI_API_SERVER}"
    fi
    if [ -n "${LAMBDA_AUTH_TOKEN:-}" ]; then
        set_override LAMBDA_AUTH_TOKEN "${LAMBDA_AUTH_TOKEN}"
    fi
    if [ -n "${EVENTBRIDGE_SCHEDULER_ROLE_ARN:-}" ]; then
        set_override EVENTBRIDGE_SCHEDULER_ROLE_ARN \
            "${EVENTBRIDGE_SCHEDULER_ROLE_ARN}"
    fi
    if [ -n "${CLEANUP_RETRY_DELAY_MINUTES:-}" ]; then
        if ! [[ "${CLEANUP_RETRY_DELAY_MINUTES}" =~ ^[1-9][0-9]*$ ]]; then
            echo "==> ERROR: CLEANUP_RETRY_DELAY_MINUTES must be a" \
                 "positive integer, got:" \
                 "${CLEANUP_RETRY_DELAY_MINUTES}" >&2
            exit 1
        fi
        set_override CLEANUP_RETRY_DELAY_MINUTES \
            "${CLEANUP_RETRY_DELAY_MINUTES}"
    fi
    set_override ENVIRONMENT "${ENVIRONMENT}"
    set_override CHALLENGE_CLEANUP_LAMBDA_ARN "${FUNCTION_ARN}"

    MERGED_ENV_JSON="$(jq -n \
        --argjson existing "${EXISTING_ENV_JSON}" \
        --argjson overrides "${OVERRIDES_JSON}" \
        '$existing + $overrides')"

    MISSING="$(jq -r '
        . as $env
        | ["ECS_CLUSTER","EVALAI_API_SERVER","LAMBDA_AUTH_TOKEN",
           "EVENTBRIDGE_SCHEDULER_ROLE_ARN"]
        | map(select(. as $name | (($env[$name] // "") | length) == 0))
        | join(", ")
    ' <<<"${MERGED_ENV_JSON}")"
    if [ -n "${MISSING}" ]; then
        echo "==> ERROR: missing required config with no existing value" \
             "set: ${MISSING}" >&2
        echo "    Pass these on first deploy of a function." >&2
        exit 1
    fi

    ENV_FILE="${BUILD_DIR}/environment.json"
    jq -n --argjson vars "${MERGED_ENV_JSON}" '{Variables: $vars}' \
        >"${ENV_FILE}"
fi

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

if [ -z "${ENV_FILE}" ]; then
    echo "==> Done: ${FUNCTION_NAME} (code only)"
    exit 0
fi

echo "==> Updating function configuration"
CONFIG_ARGS=(
    --function-name "${FUNCTION_NAME}"
    --environment "file://${ENV_FILE}"
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
