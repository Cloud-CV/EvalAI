"""
AWS Lambda function to handle ECS worker OOM (OutOfMemory) crashes.

Triggered by EventBridge when an ECS task stops with an OOM error.
This Lambda:
1. Validates the event is an OOM crash (stoppedReason or exit code 137)
2. Reads ECS service tags to get challenge_pk
3. Scales the ECS service desired count to 0 (stops the crash-restart loop)
4. Calls the EvalAI API to set evaluation_module_error on the challenge

Environment variables required:
- ECS_CLUSTER: The ECS cluster name (e.g., "evalai-prod-cluster")
- AWS_REGION: The AWS region (e.g., "us-east-1")
- EVALAI_API_SERVER: The EvalAI API server URL (e.g., "https://eval.ai")
- LAMBDA_AUTH_TOKEN: Shared secret token for authenticating with the EvalAI API

EventBridge rule pattern:
{
    "source": ["aws.ecs"],
    "detail-type": ["ECS Task State Change"],
    "detail": {
        "lastStatus": ["STOPPED"],
        "clusterArn": ["arn:aws:ecs:REGION:ACCOUNT:cluster/CLUSTER_NAME"]
    }
}
"""

import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ECS_CLUSTER = os.environ.get("ECS_CLUSTER")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
EVALAI_API_SERVER = os.environ.get("EVALAI_API_SERVER")
LAMBDA_AUTH_TOKEN = os.environ.get("LAMBDA_AUTH_TOKEN")


def is_oom_event(detail):
    """
    Check if the ECS task state change event indicates an OOM crash.

    An OOM is identified by either:
    - stoppedReason containing "OutOfMemory"
    - Any container having exit code 137 (SIGKILL, typical of OOM killer)
    """
    stopped_reason = detail.get("stoppedReason", "")
    if "OutOfMemory" in stopped_reason:
        return True

    containers = detail.get("containers", [])
    for container in containers:
        if container.get("exitCode") == 137:
            return True

    return False


def get_challenge_pk_from_service(ecs_client, cluster, service_name):
    """
    Look up the challenge_pk tag from an ECS service.

    Returns the challenge_pk string or None if not found.
    """
    try:
        response = ecs_client.describe_services(
            cluster=cluster,
            services=[service_name],
        )
        services = response.get("services", [])
        if not services:
            logger.warning(
                "Service %s not found in cluster %s", service_name, cluster
            )
            return None

        tags = services[0].get("tags", [])
        for tag in tags:
            if tag.get("key") == "challenge_pk":
                return tag.get("value")

        logger.warning(
            "challenge_pk tag not found on service %s", service_name
        )
        return None
    except ClientError as e:
        logger.error("Error describing service %s: %s", service_name, str(e))
        return None


def scale_service_to_zero(ecs_client, cluster, service_name):
    """
    Scale the ECS service desired count to 0 to stop the OOM crash-restart loop.
    """
    try:
        ecs_client.update_service(
            cluster=cluster,
            service=service_name,
            desiredCount=0,
        )
        logger.info(
            "Scaled service %s to 0 in cluster %s", service_name, cluster
        )
        return True
    except ClientError as e:
        logger.error(
            "Failed to scale service %s to 0: %s", service_name, str(e)
        )
        return False


def get_worker_memory(ecs_client, task_definition_arn):
    """
    Get the memory (in MB) configured for the task definition.
    """
    try:
        response = ecs_client.describe_task_definition(
            taskDefinition=task_definition_arn
        )
        memory = response.get("taskDefinition", {}).get("memory", "unknown")
        return memory
    except ClientError:
        return "unknown"


def notify_evalai_api(challenge_pk, error_message):
    """
    Call the EvalAI API to set evaluation_module_error on the challenge.
    Uses urllib to avoid requiring the requests library in Lambda.
    """
    if not EVALAI_API_SERVER or not LAMBDA_AUTH_TOKEN:
        logger.error(
            "EVALAI_API_SERVER or LAMBDA_AUTH_TOKEN not configured. "
            "Cannot notify API."
        )
        return False

    url = (
        f"{EVALAI_API_SERVER}/api/challenges/"
        f"challenge/{challenge_pk}/update_evaluation_module_error/"
    )
    payload = json.dumps({"evaluation_module_error": error_message}).encode(
        "utf-8"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LAMBDA_AUTH_TOKEN}",
    }

    req = Request(url, data=payload, headers=headers, method="PATCH")

    try:
        with urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            logger.info(
                "Successfully notified EvalAI API for challenge %s: %s",
                challenge_pk,
                response_body,
            )
            return True
    except HTTPError as e:
        logger.error(
            "HTTP error notifying EvalAI API for challenge %s: %s %s",
            challenge_pk,
            e.code,
            e.read().decode("utf-8", errors="replace"),
        )
        return False
    except URLError as e:
        logger.error(
            "URL error notifying EvalAI API for challenge %s: %s",
            challenge_pk,
            str(e),
        )
        return False


def get_service_name_from_task(detail):
    """
    Extract the ECS service name from the task's group field.

    ECS tasks started by a service have group = "service:<service-name>".
    """
    group = detail.get("group", "")
    if group.startswith("service:"):
        return group[len("service:") :]
    return None


def handler(event, context):
    """
    Lambda handler for ECS worker OOM detection and notification.

    Receives an ECS Task State Change event from EventBridge, checks if it's
    an OOM crash, and if so:
    1. Scales the service to 0 to stop the crash loop
    2. Notifies the EvalAI API to set the error message on the challenge
    """
    detail = event.get("detail", {})

    # Only process STOPPED tasks
    if detail.get("lastStatus") != "STOPPED":
        logger.info("Ignoring non-STOPPED event: %s", detail.get("lastStatus"))
        return {"statusCode": 200, "body": "Not a STOPPED event, skipping."}

    # Check if this is an OOM event
    if not is_oom_event(detail):
        logger.info(
            "Task stopped but not due to OOM. Reason: %s",
            detail.get("stoppedReason", "unknown"),
        )
        return {"statusCode": 200, "body": "Not an OOM event, skipping."}

    # Extract service name from task group
    service_name = get_service_name_from_task(detail)
    if not service_name:
        logger.warning(
            "Could not determine service name from task group: %s",
            detail.get("group", ""),
        )
        return {"statusCode": 400, "body": "Could not determine service name."}

    logger.info(
        "OOM detected for service %s. Reason: %s",
        service_name,
        detail.get("stoppedReason", "unknown"),
    )

    ecs_client = boto3.client("ecs", region_name=AWS_REGION)

    # Get challenge_pk from service tags
    challenge_pk = get_challenge_pk_from_service(
        ecs_client, ECS_CLUSTER, service_name
    )
    if not challenge_pk:
        logger.error(
            "Could not find challenge_pk for service %s. "
            "Service may not have challenge_pk tag.",
            service_name,
        )
        return {
            "statusCode": 400,
            "body": f"No challenge_pk tag found for service {service_name}.",
        }

    # Get the worker memory from the task definition
    task_definition_arn = detail.get("taskDefinitionArn", "")
    worker_memory = get_worker_memory(ecs_client, task_definition_arn)

    # Scale service to 0 to stop the crash loop
    scale_service_to_zero(ecs_client, ECS_CLUSTER, service_name)

    # Notify the EvalAI API
    error_message = (
        f"Worker stopped: OutOfMemoryError. "
        f"Current memory: {worker_memory} MB. "
        f"Increase worker memory via Scale Resources and restart the worker."
    )
    notify_evalai_api(challenge_pk, error_message)

    logger.info(
        "OOM handling completed for challenge %s (service: %s)",
        challenge_pk,
        service_name,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"OOM handled for challenge {challenge_pk}",
                "service": service_name,
                "worker_memory": worker_memory,
            }
        ),
    }
