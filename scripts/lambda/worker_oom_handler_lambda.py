"""
AWS Lambda function to handle ECS worker OOM (OutOfMemory) crashes.

Triggered by EventBridge when an ECS task stops with an OOM error.
This Lambda:
1. Validates the event is an OOM crash (stoppedReason or exit code 137)
2. Reads ECS service tags to get challenge_pk
3. Checks if the event is stale (task def already upgraded)
4. Increases worker memory by 1 GB, upgrading CPU tier if needed
5. Registers a new task definition and force-deploys the service
6. Calls the EvalAI API to update the challenge model and send email

If the maximum Fargate memory (30 GB at 4 vCPU) is already reached,
scales the service to 0 and notifies the team.

Environment variables required:
- ECS_CLUSTER: The ECS cluster name (e.g., "evalai-prod-cluster")
- AWS_REGION: The AWS region (auto-set by Lambda runtime)
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

# Fargate CPU-to-max-memory mapping (memory in MiB).
# Each tier supports 1024 MiB increments up to the listed max.
# vCPU costs ~9x more per unit than memory, so we exhaust memory
# headroom within a CPU tier before upgrading to the next tier.
FARGATE_CPU_MEMORY_TIERS = [
    (512, 4096),
    (1024, 8192),
    (2048, 16384),
    (4096, 30720),
]

MEMORY_INCREMENT = 1024

# Read-only fields returned by describe_task_definition that must be
# stripped before re-registering.
TASK_DEF_READONLY_FIELDS = [
    "taskDefinitionArn",
    "revision",
    "status",
    "requiresAttributes",
    "compatibilities",
    "registeredAt",
    "registeredBy",
    "deregisteredAt",
]


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


def get_service_name_from_task(detail):
    """
    Extract the ECS service name from the task's group field.

    ECS tasks started by a service have group = "service:<service-name>".
    """
    group = detail.get("group", "")
    if group.startswith("service:"):
        return group[len("service:") :]
    return None


def is_stale_event(ecs_client, cluster, service_name, event_task_def_arn):
    """
    Check if the OOM event is from an outdated task definition.

    When we upgrade memory, the service gets a new task def. Old tasks that
    were launched before the upgrade may still OOM and fire events. We skip
    those to avoid double-incrementing memory.

    Returns True if the event's task def doesn't match the service's current one.
    """
    try:
        response = ecs_client.describe_services(
            cluster=cluster, services=[service_name]
        )
        services = response.get("services", [])
        if not services:
            return False
        current_task_def = services[0].get("taskDefinition", "")
        if current_task_def != event_task_def_arn:
            logger.info(
                "Stale OOM event: event task def %s != service task def %s",
                event_task_def_arn,
                current_task_def,
            )
            return True
        return False
    except ClientError as e:
        logger.error("Error checking for stale event: %s", str(e))
        return False


def get_next_memory_cpu_tier(current_memory, current_cpu):
    """
    Calculate the next memory and CPU values after an OOM.

    Increments memory by 1 GB (1024 MiB). Always returns the smallest
    (cheapest) valid CPU tier for the new memory -- vCPU is ~9x more
    expensive than memory on Fargate, so we optimise for cost rather
    than preserving the host's current CPU setting.

    Returns (new_memory, new_cpu) or None if already at Fargate's max.
    """
    new_memory = current_memory + MEMORY_INCREMENT

    for cpu, max_memory in FARGATE_CPU_MEMORY_TIERS:
        if new_memory <= max_memory:
            return (new_memory, cpu)

    return None


def clone_task_definition_with_memory(
    ecs_client, task_def_arn, new_memory, new_cpu
):
    """
    Clone an existing task definition with updated memory and CPU.

    Describes the current task definition, strips read-only fields,
    updates memory/cpu, and registers a new revision.

    Returns the new task definition ARN, or None on failure.
    """
    try:
        response = ecs_client.describe_task_definition(
            taskDefinition=task_def_arn
        )
        task_def = response["taskDefinition"]
    except ClientError as e:
        logger.error(
            "Failed to describe task definition %s: %s", task_def_arn, str(e)
        )
        return None

    for field in TASK_DEF_READONLY_FIELDS:
        task_def.pop(field, None)

    task_def["memory"] = str(new_memory)
    task_def["cpu"] = str(new_cpu)

    try:
        response = ecs_client.register_task_definition(**task_def)
        new_arn = response["taskDefinition"]["taskDefinitionArn"]
        logger.info(
            "Registered new task definition %s (memory=%s, cpu=%s)",
            new_arn,
            new_memory,
            new_cpu,
        )
        return new_arn
    except ClientError as e:
        logger.error("Failed to register new task definition: %s", str(e))
        return None


def update_service_with_new_task_def(
    ecs_client, cluster, service_name, task_def_arn
):
    """
    Update the ECS service to use a new task definition and force a new deployment.
    """
    try:
        ecs_client.update_service(
            cluster=cluster,
            service=service_name,
            taskDefinition=task_def_arn,
            forceNewDeployment=True,
        )
        logger.info(
            "Updated service %s with task def %s (force new deployment)",
            service_name,
            task_def_arn,
        )
        return True
    except ClientError as e:
        logger.error("Failed to update service %s: %s", service_name, str(e))
        return False


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


def notify_evalai_api(challenge_pk, payload):
    """
    Call the EvalAI API to update challenge fields and optionally send email.
    Uses urllib to avoid requiring the requests library in Lambda.

    payload is a dict that may contain:
    - evaluation_module_error (str)
    - worker_memory (int)
    - worker_cpu_cores (int)
    - task_def_arn (str)
    - send_email (bool)
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
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LAMBDA_AUTH_TOKEN}",
    }

    req = Request(url, data=data, headers=headers, method="PATCH")

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


def handler(event, context):
    """
    Lambda handler for ECS worker OOM detection and auto-retry.

    Receives an ECS Task State Change event from EventBridge, checks if it's
    an OOM crash, and if so:
    1. Checks if this is a stale event (already handled)
    2. Calculates the next memory/CPU tier
    3. If within Fargate limits: registers new task def, updates service, notifies API
    4. If at max: scales to 0 and notifies API
    """
    detail = event.get("detail", {})

    if detail.get("lastStatus") != "STOPPED":
        logger.info("Ignoring non-STOPPED event: %s", detail.get("lastStatus"))
        return {"statusCode": 200, "body": "Not a STOPPED event, skipping."}

    if not is_oom_event(detail):
        logger.info(
            "Task stopped but not due to OOM. Reason: %s",
            detail.get("stoppedReason", "unknown"),
        )
        return {"statusCode": 200, "body": "Not an OOM event, skipping."}

    service_name = get_service_name_from_task(detail)
    if not service_name:
        logger.warning(
            "Could not determine service name from task group: %s",
            detail.get("group", ""),
        )
        return {"statusCode": 400, "body": "Could not determine service name."}

    event_task_def_arn = detail.get("taskDefinitionArn", "")

    logger.info(
        "OOM detected for service %s (task def: %s). Reason: %s",
        service_name,
        event_task_def_arn,
        detail.get("stoppedReason", "unknown"),
    )

    ecs_client = boto3.client("ecs", region_name=AWS_REGION)

    # Skip stale events from old task definitions
    if is_stale_event(
        ecs_client, ECS_CLUSTER, service_name, event_task_def_arn
    ):
        return {
            "statusCode": 200,
            "body": "Stale OOM event (task def already upgraded), skipping.",
        }

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

    # Get current memory/CPU from the task definition
    try:
        td_response = ecs_client.describe_task_definition(
            taskDefinition=event_task_def_arn
        )
        td = td_response["taskDefinition"]
        current_memory = int(td.get("memory", "1024"))
        current_cpu = int(td.get("cpu", "512"))
    except (ClientError, ValueError) as e:
        logger.error("Failed to get task def details: %s", str(e))
        scale_service_to_zero(ecs_client, ECS_CLUSTER, service_name)
        notify_evalai_api(
            challenge_pk,
            {
                "evaluation_module_error": (
                    "Worker stopped: OutOfMemoryError. "
                    "Could not read current memory configuration. "
                    "Please increase worker memory manually and restart."
                ),
                "send_email": True,
            },
        )
        return {"statusCode": 500, "body": "Failed to read task definition."}

    next_tier = get_next_memory_cpu_tier(current_memory, current_cpu)

    if next_tier is None:
        # Already at Fargate's maximum -- stop and notify
        logger.warning(
            "Challenge %s already at max Fargate memory (%s MB, CPU %s). "
            "Scaling to 0.",
            challenge_pk,
            current_memory,
            current_cpu,
        )
        scale_service_to_zero(ecs_client, ECS_CLUSTER, service_name)
        notify_evalai_api(
            challenge_pk,
            {
                "evaluation_module_error": (
                    f"Worker stopped: OutOfMemoryError. "
                    f"Current memory: {current_memory} MB (CPU: {current_cpu}). "
                    f"Maximum Fargate memory reached. "
                    f"The evaluation script needs to be optimized to use less memory."
                ),
                "send_email": True,
            },
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Max memory reached for challenge {challenge_pk}",
                    "current_memory": current_memory,
                    "current_cpu": current_cpu,
                }
            ),
        }

    new_memory, new_cpu = next_tier
    logger.info(
        "Auto-increasing memory for challenge %s: %s -> %s MB (CPU: %s -> %s)",
        challenge_pk,
        current_memory,
        new_memory,
        current_cpu,
        new_cpu,
    )

    # Register new task definition with increased memory
    new_task_def_arn = clone_task_definition_with_memory(
        ecs_client, event_task_def_arn, new_memory, new_cpu
    )
    if not new_task_def_arn:
        scale_service_to_zero(ecs_client, ECS_CLUSTER, service_name)
        notify_evalai_api(
            challenge_pk,
            {
                "evaluation_module_error": (
                    f"Worker stopped: OutOfMemoryError. "
                    f"Failed to register new task definition with {new_memory} MB. "
                    f"Please increase worker memory manually and restart."
                ),
                "send_email": True,
            },
        )
        return {
            "statusCode": 500,
            "body": "Failed to register new task definition.",
        }

    # Update service with new task definition
    if not update_service_with_new_task_def(
        ecs_client, ECS_CLUSTER, service_name, new_task_def_arn
    ):
        scale_service_to_zero(ecs_client, ECS_CLUSTER, service_name)
        notify_evalai_api(
            challenge_pk,
            {
                "evaluation_module_error": (
                    f"Worker stopped: OutOfMemoryError. "
                    f"New task definition registered ({new_memory} MB) but "
                    f"failed to update the service. "
                    f"Please restart the worker manually."
                ),
                "task_def_arn": new_task_def_arn,
                "worker_memory": new_memory,
                "worker_cpu_cores": new_cpu,
                "send_email": True,
            },
        )
        return {"statusCode": 500, "body": "Failed to update service."}

    # Notify API to update model fields and send email
    notify_evalai_api(
        challenge_pk,
        {
            "evaluation_module_error": (
                f"Worker OOM detected. Auto-increased memory: "
                f"{current_memory} -> {new_memory} MB "
                f"(CPU: {current_cpu} -> {new_cpu}). "
                f"Worker is restarting with the new configuration."
            ),
            "worker_memory": new_memory,
            "worker_cpu_cores": new_cpu,
            "task_def_arn": new_task_def_arn,
            "send_email": True,
        },
    )

    logger.info(
        "OOM auto-retry completed for challenge %s: memory %s -> %s, CPU %s -> %s",
        challenge_pk,
        current_memory,
        new_memory,
        current_cpu,
        new_cpu,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"OOM auto-retry for challenge {challenge_pk}",
                "service": service_name,
                "old_memory": current_memory,
                "new_memory": new_memory,
                "old_cpu": current_cpu,
                "new_cpu": new_cpu,
                "task_def_arn": new_task_def_arn,
            }
        ),
    }
