#!/usr/bin/env bash
#
# Deploy the EKS node autoscale Lambda and its supporting AWS configuration.
#
# The function's code, failure handling, and reconciliation schedule were
# previously configured by hand in the AWS console, which made drift invisible
# (e.g. an environment variable set to a name the code never read). This script
# is the single source of truth for that configuration.
#
# Usage:
#   ENVIRONMENT=production \
#   EVALAI_API_SERVER=https://eval.ai \
#   LAMBDA_AUTH_TOKEN=xxx \
#   ./scripts/lambda/deploy_auto_scale_eks_nodes_lambda.sh
#
# Optional:
#   AWS_REGION            (default us-east-1)
#   AWS_PROFILE           passed through to the AWS CLI
#   DLQ_ARN               SQS queue / SNS topic ARN for failed async invocations
#   SWEEP_SCHEDULE        EventBridge schedule expression
#                         (default "rate(10 minutes)")
#   SKIP_SCHEDULE=1       skip creating/updating the sweep schedule

set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT is required (e.g. production, staging)}"
AWS_REGION="${AWS_REGION:-us-east-1}"
SWEEP_SCHEDULE="${SWEEP_SCHEDULE:-rate(10 minutes)}"

FUNCTION_NAME="evalai-${ENVIRONMENT}-auto-scale-eks-nodes"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(mktemp -d)"
ZIP_PATH="${BUILD_DIR}/auto_scale_eks_nodes_lambda.zip"
RULE_NAME="${FUNCTION_NAME}-sweep"

trap 'rm -rf "${BUILD_DIR}"' EXIT

aws_cli() {
    if [ -n "${AWS_PROFILE:-}" ]; then
        aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" "$@"
    else
        aws --region "${AWS_REGION}" "$@"
    fi
}

echo "==> Packaging ${FUNCTION_NAME}"
cp "${SCRIPT_DIR}/auto_scale_eks_nodes_lambda.py" "${BUILD_DIR}/"
(cd "${BUILD_DIR}" && zip -q "${ZIP_PATH}" auto_scale_eks_nodes_lambda.py)

echo "==> Updating function code"
aws_cli lambda update-function-code \
    --function-name "${FUNCTION_NAME}" \
    --zip-file "fileb://${ZIP_PATH}" \
    --publish >/dev/null

aws_cli lambda wait function-updated \
    --function-name "${FUNCTION_NAME}"

if [ -n "${EVALAI_API_SERVER:-}" ] && [ -n "${LAMBDA_AUTH_TOKEN:-}" ]; then
    echo "==> Updating function configuration"
    ENV_VARS="EVALAI_API_SERVER=${EVALAI_API_SERVER},LAMBDA_AUTH_TOKEN=${LAMBDA_AUTH_TOKEN}"
    if [ -n "${EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME:-}" ]; then
        ENV_VARS="${ENV_VARS},EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME=${EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME}"
    fi

    CONFIG_ARGS=(
        --function-name "${FUNCTION_NAME}"
        --environment "Variables={${ENV_VARS}}"
        --timeout 300
    )
    # Async invocations that raise are retried and then routed here, which is
    # what makes autoscale failures visible instead of silently dropped.
    if [ -n "${DLQ_ARN:-}" ]; then
        CONFIG_ARGS+=(--dead-letter-config "TargetArn=${DLQ_ARN}")
    fi

    aws_cli lambda update-function-configuration "${CONFIG_ARGS[@]}" >/dev/null
    aws_cli lambda wait function-updated --function-name "${FUNCTION_NAME}"
else
    echo "==> Skipping configuration update" \
         "(set EVALAI_API_SERVER and LAMBDA_AUTH_TOKEN to apply)"
fi

if [ "${SKIP_SCHEDULE:-0}" = "1" ]; then
    echo "==> Skipping sweep schedule (SKIP_SCHEDULE=1)"
    exit 0
fi

echo "==> Configuring reconciliation sweep (${SWEEP_SCHEDULE})"
FUNCTION_ARN="$(aws_cli lambda get-function \
    --function-name "${FUNCTION_NAME}" \
    --query "Configuration.FunctionArn" --output text)"

aws_cli events put-rule \
    --name "${RULE_NAME}" \
    --schedule-expression "${SWEEP_SCHEDULE}" \
    --description "Reconciles EvalAI EKS nodegroup scaling for all eligible challenges" >/dev/null

# Idempotent: the statement may already exist from a previous deploy. Only
# that conflict is ignored — swallowing every failure here would let a deploy
# report success while leaving EventBridge unable to invoke the function, so
# the sweep would never run and nothing would say so.
RULE_ARN="$(aws_cli events describe-rule --name "${RULE_NAME}" \
    --query "Arn" --output text)"

if ! ADD_PERMISSION_OUTPUT="$(aws_cli lambda add-permission \
    --function-name "${FUNCTION_NAME}" \
    --statement-id "${RULE_NAME}-invoke" \
    --action "lambda:InvokeFunction" \
    --principal events.amazonaws.com \
    --source-arn "${RULE_ARN}" 2>&1)"; then
    if ! grep -q "ResourceConflictException" <<<"${ADD_PERMISSION_OUTPUT}"; then
        echo "${ADD_PERMISSION_OUTPUT}" >&2
        exit 1
    fi
    echo "    invoke permission already present"
fi

# The target must be passed as JSON, not CLI shorthand: shorthand cannot
# express an Input value containing braces and quotes, and rejects it with
# "Expected: '=', received: '\"'". A target registered without this Input
# makes EventBridge invoke the Lambda with an empty event, which the handler
# treats as a malformed single-challenge invocation, so the sweep never runs.
TARGETS_PATH="${BUILD_DIR}/sweep-target.json"
cat > "${TARGETS_PATH}" <<EOF
[{"Id":"1","Arn":"${FUNCTION_ARN}","Input":"{\"sweep\":true}"}]
EOF

aws_cli events put-targets \
    --rule "${RULE_NAME}" \
    --targets "file://${TARGETS_PATH}" >/dev/null

# put-targets reports per-entry failures in the response body instead of a
# non-zero exit code, so a silently unregistered target would otherwise look
# like a successful deploy.
REGISTERED_INPUT="$(aws_cli events list-targets-by-rule \
    --rule "${RULE_NAME}" \
    --query "Targets[?Id=='1'].Input | [0]" --output text)"

if [ "${REGISTERED_INPUT}" != '{"sweep":true}' ]; then
    echo "Sweep target is not registered with the expected input." >&2
    echo "Expected: {\"sweep\":true}" >&2
    echo "Found:    ${REGISTERED_INPUT}" >&2
    exit 1
fi

echo "==> Done: ${FUNCTION_NAME}"
