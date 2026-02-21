"""
AWS Lambda function to clean up EvalAI challenge resources when a challenge ends.

Triggered by EventBridge Scheduler at the challenge's end_date. Cleans up:
- ECS Fargate service (scale to 0, then delete)
- Application Auto Scaling (scalable target + policies)
- CloudWatch alarms (scale-up and scale-down)
- ECS task definition (deregister)
- CloudWatch log group

Environment variables required:
- ECS_CLUSTER: The ECS cluster name (e.g., "evalai-prod-cluster")
- AWS_REGION: The AWS region (e.g., "us-east-1")
- ENVIRONMENT: The deployment environment (e.g., "staging" or "production")

Event payload (from EventBridge Scheduler):
{
    "challenge_pk": 123,
    "queue_name": "challenge-queue-name"
}
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ECS_CLUSTER = os.environ.get("ECS_CLUSTER")
AWS_REGION = os.environ.get("AWS_REGION")
ENVIRONMENT = os.environ.get("ENVIRONMENT")


def handler(event, context):
    """
    Lambda handler for challenge resource cleanup.
    """
    challenge_pk = event.get("challenge_pk")
    queue_name = event.get("queue_name")

    if not challenge_pk or not queue_name:
        logger.error("Missing challenge_pk or queue_name in event: %s", event)
        return {"statusCode": 400, "body": "Missing required fields"}

    service_name = f"{queue_name}_service"
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

    try:
        response = ecs.delete_service(
            cluster=ECS_CLUSTER, service=service_name, force=True
        )
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
        logger.info(
            "Service deletion skipped for %s: %s",
            service_name,
            e.response["Error"]["Code"],
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
