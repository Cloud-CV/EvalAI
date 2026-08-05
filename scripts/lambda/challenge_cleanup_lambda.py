"""
AWS Lambda function to clean up EvalAI challenge resources when a challenge ends.

Triggered by EventBridge Scheduler at the challenge's end_date. Before
tearing anything down, checks whether the challenge still has pending
submissions (running/submitted/queued/resuming). If so, cleanup is skipped
and a new one-time schedule is created to re-check later — the worker stays
up so it can keep draining the queue. Once nothing is pending, cleans up:
- ECS Fargate service (scale to 0, then delete)
- Application Auto Scaling (scalable target + policies)
- CloudWatch alarms (scale-up and scale-down)
- ECS task definition (deregister)
- CloudWatch log group

Environment variables required:
- ECS_CLUSTER: The ECS cluster name (e.g., "evalai-prod-cluster")
- AWS_REGION: The AWS region (e.g., "us-east-1")
- ENVIRONMENT: The deployment environment (e.g., "staging" or "production")
- EVALAI_API_SERVER: EvalAI API server URL (e.g. https://eval.ai), used to
  check pending submissions before deleting anything
- LAMBDA_AUTH_TOKEN: shared secret for internal Lambda-auth APIs
- EVENTBRIDGE_SCHEDULER_ROLE_ARN: role EventBridge Scheduler assumes to
  invoke this Lambda, needed to recreate the schedule on retry
- CHALLENGE_CLEANUP_LAMBDA_ARN: this Lambda's own ARN, needed to recreate
  the schedule on retry
- CLEANUP_RETRY_DELAY_MINUTES: minutes to wait before re-checking pending
  submissions (optional, defaults to 60)

Event payload (from EventBridge Scheduler):
{
    "challenge_pk": 123,
    "queue_name": "challenge-queue-name"
}
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import ClientError

ECS_RESOURCE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def get_ecs_service_name(queue_name):
    """Return ECS-safe service name from an SQS queue name."""
    base = queue_name[:-5] if queue_name.endswith(".fifo") else queue_name
    base = ECS_RESOURCE_NAME_PATTERN.sub("-", base)
    return f"{base}_service"


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ECS_CLUSTER = os.environ.get("ECS_CLUSTER")
AWS_REGION = os.environ.get("AWS_REGION")
ENVIRONMENT = os.environ.get("ENVIRONMENT")
EVALAI_API_SERVER = os.environ.get("EVALAI_API_SERVER")
LAMBDA_AUTH_TOKEN = os.environ.get("LAMBDA_AUTH_TOKEN")
EVENTBRIDGE_SCHEDULER_ROLE_ARN = os.environ.get(
    "EVENTBRIDGE_SCHEDULER_ROLE_ARN"
)
CHALLENGE_CLEANUP_LAMBDA_ARN = os.environ.get("CHALLENGE_CLEANUP_LAMBDA_ARN")
CLEANUP_RETRY_DELAY_MINUTES = int(
    os.environ.get("CLEANUP_RETRY_DELAY_MINUTES", "60")
)


def get_pending_submission_count(challenge_pk):
    """
    Return pending submission count for a challenge via the internal EvalAI
    API. Raises on failure so callers can fail safe (skip deletion).
    """
    if not EVALAI_API_SERVER or not LAMBDA_AUTH_TOKEN:
        raise RuntimeError(
            "EVALAI_API_SERVER or LAMBDA_AUTH_TOKEN not configured."
        )

    challenge_pk = int(challenge_pk)
    url = (
        f"{EVALAI_API_SERVER.rstrip('/')}/api/challenges/challenge/"
        f"{challenge_pk}/pending_submission_count/"
    )
    headers = {"Authorization": f"Bearer {LAMBDA_AUTH_TOKEN}"}
    request = Request(url=url, headers=headers, method="GET")
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["pending_submissions"]


def clear_challenge_worker_state(challenge_pk):
    """
    Clear Challenge.workers / task_def_arn after ECS resources are gone.

    handle_end_date_change and ensure_workers_for_submission treat
    workers is None as "stack was cleaned up; recreate on demand". Leaving
    a stale workers > 0 after this Lambda deletes the ECS service blocks
    that recreate path and leaves submissions with no consumers.
    """
    if not EVALAI_API_SERVER or not LAMBDA_AUTH_TOKEN:
        raise RuntimeError(
            "EVALAI_API_SERVER or LAMBDA_AUTH_TOKEN not configured."
        )

    challenge_pk = int(challenge_pk)
    url = (
        f"{EVALAI_API_SERVER.rstrip('/')}/api/challenges/challenge/"
        f"{challenge_pk}/clear_worker_state/"
    )
    headers = {
        "Authorization": f"Bearer {LAMBDA_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    request = Request(url=url, data=b"{}", headers=headers, method="POST")
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"clear_worker_state failed for challenge {challenge_pk}: "
            f"HTTP {e.code} {body}"
        ) from e
    except URLError as e:
        raise RuntimeError(
            f"clear_worker_state failed for challenge {challenge_pk}: {e}"
        ) from e
    return payload


def reschedule_cleanup(challenge_pk, queue_name):
    """
    Create a new one-time EventBridge schedule to re-check this challenge
    for cleanup after CLEANUP_RETRY_DELAY_MINUTES. Mirrors
    schedule_challenge_cleanup in apps/challenges/aws_utils.py.

    Important: ActionAfterCompletion=DELETE only removes the *invoking*
    schedule after this Lambda invocation completes. During the run the
    original name still exists, so create_schedule with the same name
    raises ConflictException. Use a unique retry name so pending
    challenges keep getting re-checked instead of permanently losing
    their cleanup schedule after EventBridge exhausts retries.

    Returns True on success, False on failure (logged) so the caller can
    surface the failure instead of reporting a false success.
    """
    if not CHALLENGE_CLEANUP_LAMBDA_ARN or not EVENTBRIDGE_SCHEDULER_ROLE_ARN:
        logger.error(
            "CHALLENGE_CLEANUP_LAMBDA_ARN or EVENTBRIDGE_SCHEDULER_ROLE_ARN "
            "not set. Cannot reschedule cleanup for challenge %s.",
            challenge_pk,
        )
        return False

    retry_at = datetime.utcnow() + timedelta(
        minutes=CLEANUP_RETRY_DELAY_MINUTES
    )
    # Unique suffix avoids ConflictException with the still-active invoking
    # schedule. Keep within EventBridge Scheduler's 64-char name limit.
    schedule_name = (
        f"evalai-cleanup-challenge-{ENVIRONMENT}-{challenge_pk}"
        f"-r{int(retry_at.timestamp())}"
    )
    if len(schedule_name) > 64:
        # Fall back to a shorter unique name if env/pk are unusually long.
        schedule_name = (
            f"evalai-cln-{challenge_pk}-r{int(retry_at.timestamp())}"
        )
        schedule_name = schedule_name[:64]
    schedule_expression = "at({})".format(
        retry_at.strftime("%Y-%m-%dT%H:%M:%S")
    )

    scheduler_client = boto3.client("scheduler", region_name=AWS_REGION)
    try:
        scheduler_client.create_schedule(
            Name=schedule_name,
            ScheduleExpression=schedule_expression,
            ScheduleExpressionTimezone="UTC",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": CHALLENGE_CLEANUP_LAMBDA_ARN,
                "RoleArn": EVENTBRIDGE_SCHEDULER_ROLE_ARN,
                "Input": json.dumps(
                    {"challenge_pk": challenge_pk, "queue_name": queue_name}
                ),
            },
            ActionAfterCompletion="DELETE",
        )
        logger.info(
            "Rescheduled cleanup for challenge %s at %s (schedule %s)",
            challenge_pk,
            retry_at,
            schedule_name,
        )
        return True
    except ClientError as e:
        logger.exception(
            "Failed to reschedule cleanup for challenge %s: %s",
            challenge_pk,
            e,
        )
        return False


def handler(event, context):
    """
    Lambda handler for challenge resource cleanup.
    """
    challenge_pk = event.get("challenge_pk")
    queue_name = event.get("queue_name")

    if not challenge_pk or not queue_name:
        logger.error("Missing challenge_pk or queue_name in event: %s", event)
        return {"statusCode": 400, "body": "Missing required fields"}

    try:
        pending_submissions = get_pending_submission_count(challenge_pk)
    except Exception as e:  # noqa: BLE001 - any failure here must fail safe
        logger.error(
            "Failed to check pending submissions for challenge %s: %s. "
            "Skipping cleanup and rescheduling to be safe.",
            challenge_pk,
            e,
        )
        if not reschedule_cleanup(challenge_pk, queue_name):
            raise RuntimeError(
                f"Could not verify pending submissions for challenge "
                f"{challenge_pk} and failed to reschedule cleanup; "
                f"needs manual attention."
            ) from e
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Could not verify pending submissions for "
                    f"challenge {challenge_pk}; rescheduled cleanup.",
                }
            ),
        }

    if pending_submissions > 0:
        logger.info(
            "Challenge %s has %s pending submission(s); skipping cleanup "
            "and rescheduling.",
            challenge_pk,
            pending_submissions,
        )
        if not reschedule_cleanup(challenge_pk, queue_name):
            raise RuntimeError(
                f"Challenge {challenge_pk} has pending submissions but "
                f"failed to reschedule cleanup; needs manual attention."
            )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Challenge {challenge_pk} has pending "
                    f"submissions; rescheduled cleanup.",
                    "pending_submissions": pending_submissions,
                }
            ),
        }

    service_name = get_ecs_service_name(queue_name)
    resource_id = f"service/{ECS_CLUSTER}/{service_name}"
    log_group_name = f"challenge-pk-{challenge_pk}-{ENVIRONMENT}-workers"

    logger.info(
        "Starting cleanup for challenge %s (service: %s)",
        challenge_pk,
        service_name,
    )

    ecs = boto3.client("ecs", region_name=AWS_REGION)
    autoscaling = boto3.client(
        "application-autoscaling", region_name=AWS_REGION
    )
    cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)
    logs = boto3.client("logs", region_name=AWS_REGION)

    # 1. Deregister auto-scaling (also removes scaling policies)
    try:
        autoscaling.deregister_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
        )
        logger.info("Deregistered scalable target for %s", service_name)
    except ClientError as e:
        logger.info(
            "Scalable target deregister skipped for %s: %s",
            service_name,
            e.response["Error"]["Code"],
        )

    # 2. Delete CloudWatch alarms
    try:
        cloudwatch.delete_alarms(
            AlarmNames=[
                f"{service_name}_scale_up",
                f"{service_name}_scale_down",
            ]
        )
        logger.info("Deleted CloudWatch alarms for %s", service_name)
    except ClientError as e:
        logger.info(
            "Alarm deletion skipped for %s: %s",
            service_name,
            e.response["Error"]["Code"],
        )

    # 3. Scale ECS service to 0 and delete it
    try:
        ecs.update_service(
            cluster=ECS_CLUSTER, service=service_name, desiredCount=0
        )
        logger.info("Scaled service %s to 0", service_name)
    except ClientError as e:
        logger.info(
            "Scale-to-zero skipped for %s: %s",
            service_name,
            e.response["Error"]["Code"],
        )

    # Track whether the ECS service is gone so we only clear DB state when
    # AWS resources match the "cleaned up" contract expected by
    # handle_end_date_change (workers is None => recreate stack).
    service_gone = False
    try:
        response = ecs.delete_service(
            cluster=ECS_CLUSTER, service=service_name, force=True
        )
        service_gone = True
        logger.info("Deleted ECS service %s", service_name)

        # Get task definition ARN from the service before it's gone
        task_def_arn = response.get("service", {}).get("taskDefinition", "")
        if task_def_arn:
            try:
                ecs.deregister_task_definition(taskDefinition=task_def_arn)
                logger.info("Deregistered task definition %s", task_def_arn)
            except ClientError as e:
                logger.info(
                    "Task definition deregister skipped for %s: %s",
                    task_def_arn,
                    e.response["Error"]["Code"],
                )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        # Already absent still means cleanup succeeded for DB sync purposes.
        if error_code in (
            "ServiceNotFoundException",
            "ClusterNotFoundException",
        ):
            service_gone = True
        logger.info(
            "Service deletion skipped for %s: %s",
            service_name,
            error_code,
        )

    # 4. Delete CloudWatch log group
    try:
        logs.delete_log_group(logGroupName=log_group_name)
        logger.info("Deleted log group %s", log_group_name)
    except ClientError as e:
        logger.info(
            "Log group deletion skipped for %s: %s",
            log_group_name,
            e.response["Error"]["Code"],
        )

    if not service_gone:
        raise RuntimeError(
            f"ECS service {service_name} still exists after cleanup attempt "
            f"for challenge {challenge_pk}; refusing to clear DB worker state."
        )

    # 5. Sync Django state so end-date extensions / new submissions can
    # recreate the worker stack (workers is None is the recreate signal).
    try:
        clear_challenge_worker_state(challenge_pk)
    except Exception as e:  # noqa: BLE001 - surface any sync failure
        raise RuntimeError(
            f"ECS resources cleaned for challenge {challenge_pk} but failed "
            f"to clear DB worker state; needs manual attention "
            f"(set workers=None, task_def_arn='')."
        ) from e

    logger.info(
        "Cleanup completed for challenge %s (service: %s)",
        challenge_pk,
        service_name,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Cleanup completed for challenge {challenge_pk}",
                "service": service_name,
            }
        ),
    }
