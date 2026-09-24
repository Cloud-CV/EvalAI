import ast
import hashlib
import json
import logging
import os
import random
import re
import string
import uuid
from http import HTTPStatus

import yaml
from accounts.models import JwtToken
from base.utils import get_boto3_client
from botocore.exceptions import BotoCoreError, ClientError
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core import serializers
from django.core.files.temp import NamedTemporaryFile
from django.db import DatabaseError

from evalai.celery import app

from .challenge_notification_util import (
    construct_and_send_eks_cluster_creation_mail,
    construct_and_send_worker_start_mail,
)
from .constants import (
    DEFAULT_WORKER_PYTHON_VERSION,
    SUPPORTED_WORKER_PYTHON_VERSIONS,
    get_ecr_env_name,
)
from .task_definitions import (
    container_definition_code_upload_worker,
    container_definition_submission_worker,
    delete_service_args,
    scale_service_args,
    service_definition,
    task_definition,
    task_definition_code_upload_worker,
    task_definition_static_code_upload_worker,
    update_service_args,
)
from .worker_utils import (
    ensure_challenge_worker_python_version,
    normalize_worker_python_version,
)

logger = logging.getLogger(__name__)

DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
ENV = DJANGO_SETTINGS_MODULE.split(".")[-1]
EVALAI_DNS = os.environ.get("SERVICE_DNS")


def get_current_ecr_env():
    return get_ecr_env_name(ENV, os.environ.get("ECR_ENV"))


def load_aws_api_kwargs(formatted_kwargs):
    """
    Parse formatted ECS API kwargs without using eval().
    """
    return ast.literal_eval(formatted_kwargs)


ECS_RESOURCE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def strip_fifo_suffix(queue_name):
    """Strip the ``.fifo`` suffix from an SQS queue name.

    The suffix contains a dot which is illegal in ECS resource names
    (service names, task-definition families, container names).
    """
    if queue_name.endswith(".fifo"):
        return queue_name[:-5]
    return queue_name


def sanitize_ecs_resource_name(name):
    """Return a name safe for ECS families, services, and containers."""
    return ECS_RESOURCE_NAME_PATTERN.sub("-", strip_fifo_suffix(name))


def get_ecs_service_name(queue_name):
    """Return ECS-safe service name from a queue name."""
    return f"{sanitize_ecs_resource_name(queue_name)}_service"


def get_evalai_submission_worker_ecr_prefixes():
    """
    Return accepted ECR URL prefixes for EvalAI-managed submission worker images.
    """
    account_id = aws_keys["AWS_ACCOUNT_ID"]
    region = aws_keys["AWS_REGION"]
    base = f"{account_id}.dkr.ecr.{region}.amazonaws.com/evalai-"
    ecr_env = get_current_ecr_env()
    prefixes = {f"{base}{ecr_env}-worker-py"}
    if ecr_env != ENV:
        prefixes.add(f"{base}{ENV}-worker-py")
    return prefixes


aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get(
        "AWS_STORAGE_BUCKET_NAME", "evalai-s3-bucket"
    ),
}

CHALLENGE_CLEANUP_LAMBDA_ARN = os.environ.get(
    "CHALLENGE_CLEANUP_LAMBDA_ARN", ""
)
EVENTBRIDGE_SCHEDULER_ROLE_ARN = os.environ.get(
    "EVENTBRIDGE_SCHEDULER_ROLE_ARN", ""
)
EKS_NODE_AUTOSCALE_LAMBDA_ARN = os.environ.get(
    "EKS_NODE_AUTOSCALE_LAMBDA_ARN", ""
)
IAM_ROLE_ARN_PATTERN = re.compile(r"^arn:aws[a-zA-Z-]*:iam:")


def _resolve_eks_node_autoscale_lambda_function_name():
    """
    Return a valid Lambda FunctionName for Invoke, or empty string if
    misconfigured.

    EKS_NODE_AUTOSCALE_LAMBDA_FUNCTION_NAME takes precedence when set.
    EKS_NODE_AUTOSCALE_LAMBDA_ARN may be a full/partial Lambda ARN or a
    plain function name. IAM role ARNs are rejected with a clear log message.
    """
    function_name = os.environ.get(
        "EKS_NODE_AUTOSCALE_LAMBDA_FUNCTION_NAME", ""
    )
    if function_name:
        return function_name

    lambda_arn_or_name = EKS_NODE_AUTOSCALE_LAMBDA_ARN
    if not lambda_arn_or_name:
        return ""

    if IAM_ROLE_ARN_PATTERN.match(lambda_arn_or_name):
        logger.error(
            "EKS_NODE_AUTOSCALE_LAMBDA_ARN is set to an IAM role ARN (%s), "
            "not a Lambda function ARN or name. Configure "
            "EKS_NODE_AUTOSCALE_LAMBDA_ARN with the Lambda function ARN "
            "(e.g. arn:aws:lambda:us-east-1:ACCOUNT_ID:function:"
            "auto_scale_eks_nodes_lambda) or set "
            "EKS_NODE_AUTOSCALE_LAMBDA_FUNCTION_NAME instead.",
            lambda_arn_or_name,
        )
        return ""

    return lambda_arn_or_name


COMMON_SETTINGS_DICT = {
    "EXECUTION_ROLE_ARN": os.environ.get(
        "EXECUTION_ROLE_ARN",
        "arn:aws:iam::{}:role/evalaiTaskExecutionRole".format(
            aws_keys["AWS_ACCOUNT_ID"]
        ),
    ),
    "WORKER_IMAGE": os.environ.get(
        "WORKER_IMAGE",
        "{}.dkr.ecr.us-east-1.amazonaws.com/evalai-{}-worker-py3.9:latest".format(
            aws_keys["AWS_ACCOUNT_ID"], get_current_ecr_env()
        ),
    ),
    "CODE_UPLOAD_WORKER_IMAGE": os.environ.get(
        "CODE_UPLOAD_WORKER_IMAGE",
        "{}.dkr.ecr.us-east-1.amazonaws.com/evalai-{}-code-upload-worker:latest".format(
            aws_keys["AWS_ACCOUNT_ID"], get_current_ecr_env()
        ),
    ),
    "CIDR": os.environ.get("CIDR"),
    "CLUSTER": os.environ.get("CLUSTER", "evalai-prod-cluster"),
    "DJANGO_SERVER": os.environ.get("DJANGO_SERVER", "localhost"),
    "EVALAI_API_SERVER": os.environ.get("EVALAI_API_SERVER", "localhost"),
    "DEBUG": settings.DEBUG,
    "EMAIL_HOST": settings.EMAIL_HOST,
    "EMAIL_HOST_PASSWORD": settings.EMAIL_HOST_PASSWORD,
    "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,
    "EMAIL_PORT": settings.EMAIL_PORT,
    "EMAIL_USE_TLS": settings.EMAIL_USE_TLS,
    "MEMCACHED_LOCATION": os.environ.get("MEMCACHED_LOCATION", None),
    "RDS_DB_NAME": settings.DATABASES["default"]["NAME"],
    "RDS_HOSTNAME": settings.DATABASES["default"]["HOST"],
    "RDS_PASSWORD": settings.DATABASES["default"]["PASSWORD"],
    "RDS_USERNAME": settings.DATABASES["default"]["USER"],
    "RDS_PORT": settings.DATABASES["default"]["PORT"],
    "SECRET_KEY": settings.SECRET_KEY,
    "SENTRY_URL": os.environ.get("SENTRY_URL"),
}

VPC_DICT = {
    "SUBNET_1": os.environ.get("SUBNET_1", "subnet1"),
    "SUBNET_2": os.environ.get("SUBNET_2", "subnet2"),
    "SUBNET_SECURITY_GROUP": os.environ.get("SUBNET_SECURITY_GROUP", "sg"),
}


def get_evalai_submission_worker_ecr_image(
    python_version=None, commit_id=None
):
    """
    Return the EvalAI-managed submission worker image URI for a Python version.
    """
    python_version = python_version or DEFAULT_WORKER_PYTHON_VERSION
    if python_version not in SUPPORTED_WORKER_PYTHON_VERSIONS:
        python_version = DEFAULT_WORKER_PYTHON_VERSION
    image_tag = commit_id or "latest"
    ecr_env = get_current_ecr_env()
    return "{account}.dkr.ecr.{region}.amazonaws.com/evalai-{env}-worker-py{version}:{tag}".format(
        account=aws_keys["AWS_ACCOUNT_ID"],
        region=aws_keys["AWS_REGION"],
        env=ecr_env,
        version=python_version,
        tag=image_tag,
    )


def get_evalai_code_upload_worker_ecr_image(commit_id=None):
    """
    Return the EvalAI-managed code-upload worker image URI.
    """
    image_tag = commit_id or "latest"
    ecr_env = get_current_ecr_env()
    return "{account}.dkr.ecr.{region}.amazonaws.com/evalai-{env}-code-upload-worker:{tag}".format(
        account=aws_keys["AWS_ACCOUNT_ID"],
        region=aws_keys["AWS_REGION"],
        env=ecr_env,
        tag=image_tag,
    )


def get_deployed_worker_image_urls(commit_id=None, python_version=None):
    """
    Build canonical WORKER_IMAGE and CODE_UPLOAD_WORKER_IMAGE URLs for deploys.
    """
    python_version = python_version or DEFAULT_WORKER_PYTHON_VERSION
    return {
        "WORKER_IMAGE": get_evalai_submission_worker_ecr_image(
            python_version, commit_id
        ),
        "CODE_UPLOAD_WORKER_IMAGE": get_evalai_code_upload_worker_ecr_image(
            commit_id
        ),
    }


def is_evalai_managed_submission_worker_image(image_url):
    """
    Return True when image_url points at an EvalAI submission worker ECR repo.
    """
    if not image_url:
        return False
    return any(
        image_url.startswith(prefix)
        for prefix in get_evalai_submission_worker_ecr_prefixes()
    )


def update_evalai_worker_image_tag(image_url, commit_id):
    """
    Replace the tag on an EvalAI-managed worker image URL.
    """
    if not image_url or not commit_id or ":" not in image_url:
        return image_url
    repository, _ = image_url.rsplit(":", 1)
    return f"{repository}:{commit_id}"


def get_evalai_worker_image_tag(image_url=None, commit_id=None):
    """
    Resolve the ECR image tag for an EvalAI-managed worker image.
    """
    if commit_id:
        return commit_id
    if image_url and ":" in image_url:
        return image_url.rsplit(":", 1)[1]
    return "latest"


def get_worker_image_for_challenge(challenge, commit_id=None):
    """
    Resolve the submission worker image for a challenge.
    """
    python_version = normalize_worker_python_version(
        getattr(challenge, "worker_python_version", None)
    )

    if challenge.worker_image_url:
        if is_evalai_managed_submission_worker_image(
            challenge.worker_image_url
        ):
            image_tag = get_evalai_worker_image_tag(
                challenge.worker_image_url, commit_id
            )
            return get_evalai_submission_worker_ecr_image(
                python_version, image_tag
            )
        return challenge.worker_image_url

    return get_evalai_submission_worker_ecr_image(python_version, commit_id)


def get_image_settings_for_challenge(challenge, commit_id=None):
    """
    Build WORKER_IMAGE and CODE_UPLOAD_WORKER_IMAGE settings for task defs.
    """
    return {
        **COMMON_SETTINGS_DICT,
        "WORKER_IMAGE": get_worker_image_for_challenge(challenge, commit_id),
        "CODE_UPLOAD_WORKER_IMAGE": get_evalai_code_upload_worker_ecr_image(
            commit_id
        ),
    }


def build_task_definition_dict(
    challenge,
    queue_name,
    image_settings=None,
    worker_cpu_cores=None,
    worker_memory=None,
):
    """
    Build the ECS task definition dict for a challenge worker service.

    Returns:
        tuple: (task_definition_dict, error_response). error_response is None
        when successful.
    """
    from .utils import get_aws_credentials_for_challenge

    celery_queue_name = os.environ.get("CELERY_QUEUE_NAME")
    if not celery_queue_name:
        message = (
            "CELERY_QUEUE_NAME environment variable must be set to build "
            "worker task definitions."
        )
        return None, {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

    sqs_queue_name = queue_name
    queue_name = sanitize_ecs_resource_name(queue_name)

    container_name = f"worker_{queue_name}"
    code_upload_container_name = f"code_upload_worker_{queue_name}"
    worker_cpu_cores = (
        worker_cpu_cores
        if worker_cpu_cores is not None
        else challenge.worker_cpu_cores
    )
    worker_memory = (
        worker_memory if worker_memory is not None else challenge.worker_memory
    )
    ephemeral_storage = challenge.ephemeral_storage
    log_group_name = get_log_group_name(challenge.pk)
    AWS_SES_REGION_NAME = getattr(settings, "AWS_SES_REGION_NAME", "")
    AWS_SES_REGION_ENDPOINT = getattr(settings, "AWS_SES_REGION_ENDPOINT", "")
    updated_settings = image_settings or get_image_settings_for_challenge(
        challenge
    )
    updated_settings = {
        **updated_settings,
        "CELERY_QUEUE_NAME": celery_queue_name,
    }
    challenge_aws_keys = get_aws_credentials_for_challenge(challenge.pk)

    if challenge.is_docker_based:
        from .models import ChallengeEvaluationCluster

        try:
            cluster_details = ChallengeEvaluationCluster.objects.get(
                challenge=challenge
            )
        except ChallengeEvaluationCluster.DoesNotExist:
            message = (
                "Error. Evaluation cluster not configured for challenge "
                f"{challenge.pk}."
            )
            return None, {
                "Error": message,
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            }

        cluster_name = cluster_details.name
        cluster_endpoint = cluster_details.cluster_endpoint
        cluster_certificate = cluster_details.cluster_ssl
        efs_id = cluster_details.efs_id
        token = JwtToken.objects.get(user=challenge.creator.created_by)

        if challenge.is_static_dataset_code_upload:
            code_upload_container = (
                container_definition_code_upload_worker.format(
                    queue_name=queue_name,
                    sqs_queue_name=sqs_queue_name,
                    code_upload_container_name=code_upload_container_name,
                    auth_token=token.refresh_token,
                    cluster_name=cluster_name,
                    cluster_endpoint=cluster_endpoint,
                    certificate=cluster_certificate,
                    log_group_name=log_group_name,
                    EVALAI_DNS=EVALAI_DNS,
                    EFS_ID=efs_id,
                    **updated_settings,
                    **challenge_aws_keys,
                )
            )
            submission_container = (
                container_definition_submission_worker.format(
                    queue_name=queue_name,
                    sqs_queue_name=sqs_queue_name,
                    container_name=container_name,
                    ENV=ENV,
                    challenge_pk=challenge.pk,
                    log_group_name=log_group_name,
                    AWS_SES_REGION_NAME=AWS_SES_REGION_NAME,
                    AWS_SES_REGION_ENDPOINT=AWS_SES_REGION_ENDPOINT,
                    **updated_settings,
                    **aws_keys,
                )
            )
            definition = task_definition_static_code_upload_worker.format(
                queue_name=queue_name,
                code_upload_container=code_upload_container,
                submission_container=submission_container,
                CPU=worker_cpu_cores,
                MEMORY=worker_memory,
                ephemeral_storage=ephemeral_storage,
                **updated_settings,
            )
        else:
            definition = task_definition_code_upload_worker.format(
                queue_name=queue_name,
                sqs_queue_name=sqs_queue_name,
                code_upload_container_name=code_upload_container_name,
                ENV=ENV,
                challenge_pk=challenge.pk,
                auth_token=token.refresh_token,
                cluster_name=cluster_name,
                cluster_endpoint=cluster_endpoint,
                certificate=cluster_certificate,
                CPU=worker_cpu_cores,
                MEMORY=worker_memory,
                ephemeral_storage=ephemeral_storage,
                log_group_name=log_group_name,
                EVALAI_DNS=EVALAI_DNS,
                EFS_ID=efs_id,
                **updated_settings,
                **challenge_aws_keys,
            )
    else:
        definition = task_definition.format(
            queue_name=queue_name,
            sqs_queue_name=sqs_queue_name,
            container_name=container_name,
            ENV=ENV,
            challenge_pk=challenge.pk,
            CPU=worker_cpu_cores,
            MEMORY=worker_memory,
            ephemeral_storage=ephemeral_storage,
            log_group_name=log_group_name,
            AWS_SES_REGION_NAME=AWS_SES_REGION_NAME,
            AWS_SES_REGION_ENDPOINT=AWS_SES_REGION_ENDPOINT,
            **updated_settings,
            **challenge_aws_keys,
        )

    return load_aws_api_kwargs(definition), None


def get_capacity_provider_strategy(challenge):
    """
    Build the ECS capacityProviderStrategy list from per-challenge fields.

    Returns a list of dicts suitable for passing to client.create_service().
    Only includes providers whose weight > 0.
    Falls back to a single FARGATE_SPOT entry if both weights are 0.
    """
    strategy = []
    spot_weight = getattr(challenge, "fargate_spot_weight", 0) or 0
    spot_base = getattr(challenge, "fargate_spot_base", 0) or 0
    fg_weight = getattr(challenge, "fargate_weight", 0) or 0
    fg_base = getattr(challenge, "fargate_base", 0) or 0

    if spot_weight > 0:
        strategy.append(
            {
                "capacityProvider": "FARGATE_SPOT",
                "weight": spot_weight,
                "base": spot_base,
            }
        )
    if fg_weight > 0:
        strategy.append(
            {
                "capacityProvider": "FARGATE",
                "weight": fg_weight,
                "base": fg_base,
            }
        )
    if not strategy:
        strategy = [
            {"capacityProvider": "FARGATE_SPOT", "weight": 1, "base": 0}
        ]
    return strategy


def get_code_upload_setup_meta_for_challenge(challenge_pk):
    """
    Return the EKS cluster network and arn meta for a challenge
    Arguments:
        challenge_pk {int} --
            challenge pk for which credentails are to be fetched
    Returns:
        code_upload_meta {dict} --
            Dict containing cluster network and arn meta
    """
    from .models import ChallengeEvaluationCluster
    from .utils import get_challenge_model

    challenge = get_challenge_model(challenge_pk)
    if challenge.use_host_credentials:
        challenge_evaluation_cluster = ChallengeEvaluationCluster.objects.get(
            challenge=challenge
        )
        code_upload_meta = {
            "SUBNET_1": challenge_evaluation_cluster.subnet_1_id,
            "SUBNET_2": challenge_evaluation_cluster.subnet_2_id,
            "SUBNET_SECURITY_GROUP": challenge_evaluation_cluster.security_group_id,
            "EKS_NODEGROUP_ROLE_ARN": challenge_evaluation_cluster.node_group_arn_role,
            "EKS_CLUSTER_ROLE_ARN": challenge_evaluation_cluster.eks_arn_role,
        }
    else:
        code_upload_meta = {
            "SUBNET_1": VPC_DICT["SUBNET_1"],
            "SUBNET_2": VPC_DICT["SUBNET_2"],
            "SUBNET_SECURITY_GROUP": VPC_DICT["SUBNET_SECURITY_GROUP"],
            "EKS_NODEGROUP_ROLE_ARN": settings.EKS_NODEGROUP_ROLE_ARN,
            "EKS_CLUSTER_ROLE_ARN": settings.EKS_CLUSTER_ROLE_ARN,
        }
    return code_upload_meta


def get_log_group_name(challenge_pk):
    log_group_name = (
        f"challenge-pk-{challenge_pk}-{settings.ENVIRONMENT}-workers"
    )
    return log_group_name


def setup_auto_scaling_for_service(challenge):
    """
    Registers the ECS service as a scalable target with Application Auto Scaling
    and creates CloudWatch alarms that scale the service based on SQS queue depth.

    Scale-up: when ApproximateNumberOfMessagesVisible > 0 for 1 minute.
    Scale-down: when ApproximateNumberOfMessagesVisible AND
    ApproximateNumberOfMessagesNotVisible are both 0 for 2 minutes, so a
    worker mid-submission (message received but not yet deleted, hence
    invisible rather than gone) isn't scaled to 0 out from under it.

    The ceiling comes from challenge.max_ecs_workers so that a manual scale from the
    admin survives service recreation. All the AWS calls below are upserts keyed
    by resource id / policy name / alarm name, so this is safe to re-run to
    reconcile an existing configuration.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge whose service to configure.

    Returns:
    bool: True if the configuration was applied (or intentionally skipped),
        False if AWS rejected it.
    """
    if settings.DEBUG:
        logger.info(
            "Skipping auto-scaling setup for challenge %s in development environment.",
            challenge.pk,
        )
        return True

    queue_name = challenge.queue
    service_name = get_ecs_service_name(queue_name)
    cluster = COMMON_SETTINGS_DICT["CLUSTER"]
    resource_id = f"service/{cluster}/{service_name}"
    # A ceiling of 0 would leave the service permanently switched off, since the
    # scale-up policy sets ExactCapacity to this value.
    max_ecs_workers = max(challenge.max_ecs_workers or 1, 1)
    min_ecs_workers = min(
        max(
            (
                challenge.min_ecs_workers
                if challenge.min_ecs_workers is not None
                else 0
            ),
            0,
        ),
        max_ecs_workers,
    )

    autoscaling_client = get_boto3_client("application-autoscaling", aws_keys)

    try:
        # Register the ECS service as a scalable target
        autoscaling_client.register_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
            MinCapacity=min_ecs_workers,
            MaxCapacity=max_ecs_workers,
        )

        # Create scale-up policy
        scale_up_response = autoscaling_client.put_scaling_policy(
            PolicyName=f"{service_name}_scale_up",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
            PolicyType="StepScaling",
            StepScalingPolicyConfiguration={
                "AdjustmentType": "ExactCapacity",
                "StepAdjustments": [
                    {
                        "MetricIntervalLowerBound": 0,
                        "ScalingAdjustment": max_ecs_workers,
                    }
                ],
                "Cooldown": 60,
            },
        )
        scale_up_policy_arn = scale_up_response["PolicyARN"]

        # Create scale-down policy
        scale_down_response = autoscaling_client.put_scaling_policy(
            PolicyName=f"{service_name}_scale_down",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
            PolicyType="StepScaling",
            StepScalingPolicyConfiguration={
                "AdjustmentType": "ExactCapacity",
                "StepAdjustments": [
                    {
                        "MetricIntervalUpperBound": 0,
                        "ScalingAdjustment": min_ecs_workers,
                    }
                ],
                "Cooldown": 120,
            },
        )
        scale_down_policy_arn = scale_down_response["PolicyARN"]

        # Create CloudWatch alarms linked to the scaling policies
        cloudwatch_client = get_boto3_client("cloudwatch", aws_keys)

        # Scale-up alarm: queue depth > 0 for 1 minute
        cloudwatch_client.put_metric_alarm(
            AlarmName=f"{service_name}_scale_up",
            Namespace="AWS/SQS",
            MetricName="ApproximateNumberOfMessagesVisible",
            Dimensions=[{"Name": "QueueName", "Value": queue_name}],
            Statistic="Sum",
            Period=60,
            EvaluationPeriods=1,
            Threshold=0,
            ComparisonOperator="GreaterThanThreshold",
            AlarmActions=[scale_up_policy_arn],
        )

        # Scale-down alarm: visible + in-flight queue depth = 0 for 2 minutes.
        # ApproximateNumberOfMessagesVisible alone would hit 0 as soon as a
        # worker receives a message, even though it's still processing it
        # (in-flight messages are "not visible", not gone) - a metric-math
        # expression is used instead of a plain metric so both are checked.
        cloudwatch_client.put_metric_alarm(
            AlarmName=f"{service_name}_scale_down",
            EvaluationPeriods=1,
            Threshold=0,
            ComparisonOperator="LessThanOrEqualToThreshold",
            # SQS stops publishing these metrics once a queue's been idle for
            # a while, which would otherwise leave this alarm stuck in
            # INSUFFICIENT_DATA (and scale-down never firing) for the exact
            # "genuinely idle" case this alarm exists to catch.
            TreatMissingData="breaching",
            AlarmActions=[scale_down_policy_arn],
            Metrics=[
                {
                    "Id": "visible",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/SQS",
                            "MetricName": "ApproximateNumberOfMessagesVisible",
                            "Dimensions": [
                                {"Name": "QueueName", "Value": queue_name}
                            ],
                        },
                        "Period": 120,
                        "Stat": "Sum",
                    },
                    "ReturnData": False,
                },
                {
                    "Id": "in_flight",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/SQS",
                            "MetricName": "ApproximateNumberOfMessagesNotVisible",
                            "Dimensions": [
                                {"Name": "QueueName", "Value": queue_name}
                            ],
                        },
                        "Period": 120,
                        "Stat": "Sum",
                    },
                    "ReturnData": False,
                },
                {
                    "Id": "total_depth",
                    "Expression": "visible + in_flight",
                    "Label": "Total queue depth (visible + in-flight)",
                    "ReturnData": True,
                },
            ],
        )

        logger.info(
            "Auto-scaling configured for challenge %s"
            " (service: %s, min: %s, max: %s)",
            challenge.pk,
            service_name,
            min_ecs_workers,
            max_ecs_workers,
        )
        return True
    except ClientError as e:
        logger.exception(
            "Failed to setup auto-scaling for challenge %s: %s",
            challenge.pk,
            e,
        )
        return False


def cleanup_auto_scaling_for_service(challenge):
    """
    Removes auto-scaling configuration and CloudWatch alarms for a challenge.

    Called during service deletion or challenge cleanup. Handles cases where
    resources have already been removed gracefully.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge to clean up.
    """
    if settings.DEBUG:
        logger.info(
            "Skipping auto-scaling cleanup for challenge %s in development environment.",
            challenge.pk,
        )
        return

    queue_name = challenge.queue
    service_name = get_ecs_service_name(queue_name)
    cluster = COMMON_SETTINGS_DICT["CLUSTER"]
    resource_id = f"service/{cluster}/{service_name}"

    # Deregister scalable target (also removes scaling policies)
    try:
        autoscaling_client = get_boto3_client(
            "application-autoscaling", aws_keys
        )
        autoscaling_client.deregister_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
        )
    except ClientError:
        pass  # Already deregistered or never registered

    # Delete CloudWatch alarms
    try:
        cloudwatch_client = get_boto3_client("cloudwatch", aws_keys)
        cloudwatch_client.delete_alarms(
            AlarmNames=[
                f"{service_name}_scale_up",
                f"{service_name}_scale_down",
            ]
        )
    except ClientError:
        pass  # Already deleted or never created

    # Delete EventBridge cleanup schedule
    delete_challenge_cleanup_schedule(challenge)

    logger.info(
        "Auto-scaling cleaned up for challenge %s (service: %s)",
        challenge.pk,
        service_name,
    )


def schedule_challenge_cleanup(challenge):
    """
    Creates a one-time EventBridge Scheduler schedule that fires at the
    challenge's end_date to trigger a Lambda that cleans up all AWS resources
    (ECS service, auto-scaling, CloudWatch alarms).

    The schedule auto-deletes after firing (ActionAfterCompletion=DELETE).

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge to schedule cleanup for.
    """
    if settings.DEBUG:
        logger.info(
            "Skipping EventBridge cleanup schedule for challenge %s in development environment.",
            challenge.pk,
        )
        return

    if not CHALLENGE_CLEANUP_LAMBDA_ARN or not EVENTBRIDGE_SCHEDULER_ROLE_ARN:
        logger.warning(
            "CHALLENGE_CLEANUP_LAMBDA_ARN or EVENTBRIDGE_SCHEDULER_ROLE_ARN not set. "
            "Skipping EventBridge schedule for challenge %s.",
            challenge.pk,
        )
        return

    schedule_name = (
        f"evalai-cleanup-challenge-{settings.ENVIRONMENT}-{challenge.pk}"
    )
    # EventBridge Scheduler uses the 'at()' expression for one-time schedules
    schedule_expression = "at({})".format(
        challenge.end_date.strftime("%Y-%m-%dT%H:%M:%S")
    )

    try:
        scheduler_client = get_boto3_client("scheduler", aws_keys)
        scheduler_client.create_schedule(
            Name=schedule_name,
            ScheduleExpression=schedule_expression,
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": CHALLENGE_CLEANUP_LAMBDA_ARN,
                "RoleArn": EVENTBRIDGE_SCHEDULER_ROLE_ARN,
                "Input": json.dumps(
                    {
                        "challenge_pk": challenge.pk,
                        "queue_name": challenge.queue,
                    }
                ),
            },
            ActionAfterCompletion="DELETE",
        )
        logger.info(
            "Scheduled cleanup for challenge %s at %s",
            challenge.pk,
            challenge.end_date,
        )
    except ClientError as e:
        logger.exception(
            "Failed to schedule cleanup for challenge %s: %s",
            challenge.pk,
            e,
        )


def update_challenge_cleanup_schedule(challenge):
    """
    Updates the EventBridge Scheduler schedule for a challenge when its
    end_date changes. If the schedule doesn't exist (already fired and
    auto-deleted), creates a new one instead.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge whose schedule to update.
    """
    if settings.DEBUG:
        logger.info(
            "Skipping EventBridge schedule update for challenge %s in development environment.",
            challenge.pk,
        )
        return

    if not CHALLENGE_CLEANUP_LAMBDA_ARN or not EVENTBRIDGE_SCHEDULER_ROLE_ARN:
        logger.warning(
            "CHALLENGE_CLEANUP_LAMBDA_ARN or EVENTBRIDGE_SCHEDULER_ROLE_ARN not set. "
            "Skipping EventBridge schedule update for challenge %s.",
            challenge.pk,
        )
        return

    schedule_name = (
        f"evalai-cleanup-challenge-{settings.ENVIRONMENT}-{challenge.pk}"
    )
    schedule_expression = "at({})".format(
        challenge.end_date.strftime("%Y-%m-%dT%H:%M:%S")
    )

    try:
        scheduler_client = get_boto3_client("scheduler", aws_keys)
        scheduler_client.update_schedule(
            Name=schedule_name,
            ScheduleExpression=schedule_expression,
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": CHALLENGE_CLEANUP_LAMBDA_ARN,
                "RoleArn": EVENTBRIDGE_SCHEDULER_ROLE_ARN,
                "Input": json.dumps(
                    {
                        "challenge_pk": challenge.pk,
                        "queue_name": challenge.queue,
                    }
                ),
            },
            ActionAfterCompletion="DELETE",
        )
        logger.info(
            "Updated cleanup schedule for challenge %s to %s",
            challenge.pk,
            challenge.end_date,
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ResourceNotFoundException":
            # Schedule was already fired and auto-deleted; create a new one
            schedule_challenge_cleanup(challenge)
        else:
            logger.exception(
                "Failed to update cleanup schedule for challenge %s: %s",
                challenge.pk,
                e,
            )


def delete_challenge_cleanup_schedule(challenge):
    """
    Deletes the EventBridge Scheduler schedule for a challenge.
    Handles the case where the schedule has already been deleted gracefully.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge whose schedule to delete.
    """
    if settings.DEBUG:
        logger.info(
            "Skipping EventBridge schedule deletion for challenge %s in development environment.",
            challenge.pk,
        )
        return

    schedule_name = (
        f"evalai-cleanup-challenge-{settings.ENVIRONMENT}-{challenge.pk}"
    )
    try:
        scheduler_client = get_boto3_client("scheduler", aws_keys)
        scheduler_client.delete_schedule(Name=schedule_name)
    except ClientError:
        pass  # Schedule already deleted or never created


def schedule_challenge_cleanup_soon(challenge, delay_minutes=1):
    """
    Schedule the pending-aware cleanup Lambda to run shortly after now.

    Used when a challenge's end_date is moved into the past. EventBridge
    Scheduler rejects ``at()`` expressions in the past, so we cannot reuse
    ``schedule_challenge_cleanup`` / ``update_challenge_cleanup_schedule``
    with the new end_date. The Lambda still checks pending submissions
    before deleting ECS resources, so queued/running work can drain.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): Challenge to clean up.
    delay_minutes (int): Minutes from now to fire the schedule (default 1).
    """
    from datetime import timedelta

    from django.utils import timezone

    if settings.DEBUG:
        logger.info(
            "Skipping soon-cleanup schedule for challenge %s in development "
            "environment.",
            challenge.pk,
        )
        return

    if not CHALLENGE_CLEANUP_LAMBDA_ARN or not EVENTBRIDGE_SCHEDULER_ROLE_ARN:
        logger.warning(
            "CHALLENGE_CLEANUP_LAMBDA_ARN or EVENTBRIDGE_SCHEDULER_ROLE_ARN "
            "not set. Skipping soon-cleanup schedule for challenge %s.",
            challenge.pk,
        )
        return

    run_at = timezone.now() + timedelta(minutes=delay_minutes)
    schedule_name = (
        f"evalai-cleanup-challenge-{settings.ENVIRONMENT}-{challenge.pk}"
    )
    schedule_expression = "at({})".format(run_at.strftime("%Y-%m-%dT%H:%M:%S"))
    target = {
        "Arn": CHALLENGE_CLEANUP_LAMBDA_ARN,
        "RoleArn": EVENTBRIDGE_SCHEDULER_ROLE_ARN,
        "Input": json.dumps(
            {
                "challenge_pk": challenge.pk,
                "queue_name": challenge.queue,
            }
        ),
    }

    try:
        scheduler_client = get_boto3_client("scheduler", aws_keys)
        try:
            scheduler_client.update_schedule(
                Name=schedule_name,
                ScheduleExpression=schedule_expression,
                ScheduleExpressionTimezone="UTC",
                FlexibleTimeWindow={"Mode": "OFF"},
                Target=target,
                ActionAfterCompletion="DELETE",
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code != "ResourceNotFoundException":
                raise
            # Schedule already fired/auto-deleted; create a fresh one.
            scheduler_client.create_schedule(
                Name=schedule_name,
                ScheduleExpression=schedule_expression,
                ScheduleExpressionTimezone="UTC",
                FlexibleTimeWindow={"Mode": "OFF"},
                Target=target,
                ActionAfterCompletion="DELETE",
            )
        logger.info(
            "Scheduled soon-cleanup for challenge %s at %s",
            challenge.pk,
            run_at,
        )
    except ClientError as e:
        logger.exception(
            "Failed to schedule soon-cleanup for challenge %s: %s",
            challenge.pk,
            e,
        )


def ensure_workers_for_submission(challenge):
    """
    Ensures the worker stack (ECS service, auto-scaling, EventBridge cleanup)
    exists for a challenge when a submission is made (host or participant).
    If no active workers exist (workers is None or workers == 0), this triggers
    stack creation/start via start_workers.

    This allows both challenge hosts (pre-approval testing) and participants
    (approved challenges) to recover from missing/stopped workers.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge to ensure workers for.
    """
    if settings.DEBUG or settings.TEST:
        logger.info(
            "Skipping ensure_workers_for_submission for challenge %s "
            "in development/test environment.",
            challenge.pk,
        )
        return

    # Only applies to Fargate-managed challenges
    if (
        challenge.is_docker_based
        or challenge.uses_ec2_worker
        or challenge.remote_evaluation
    ):
        return

    # Stack already has active workers
    if challenge.workers not in (None, 0):
        return

    logger.info(
        "Submission detected for challenge %s with no active workers. "
        "Creating worker stack.",
        challenge.pk,
    )
    response = start_workers([challenge])
    count, failures = response["count"], response["failures"]
    if count:
        logger.info(
            "Worker stack created successfully for challenge %s.",
            challenge.pk,
        )
    else:
        logger.error(
            "Failed to create worker stack for challenge %s: %s",
            challenge.pk,
            failures[0]["message"] if failures else "Unknown error",
        )


def trigger_eks_node_autoscale(
    challenge_pk,
    trigger_source,
    submission_pk=None,
    submission_status=None,
    previous_submission_status=None,
):
    """
    Invoke the EKS node autoscale Lambda asynchronously.

    This is best-effort and intentionally non-blocking for submission flows.
    """
    if settings.DEBUG or settings.TEST:
        logger.info(
            "Skipping autoscale Lambda invoke for challenge %s in dev/test.",
            challenge_pk,
        )
        return

    pending_statuses = {"running", "submitted", "queued", "resuming"}
    terminal_statuses = {"finished", "failed", "cancelled"}
    normalized_status = (
        submission_status.lower()
        if isinstance(submission_status, str)
        else None
    )
    normalized_previous_status = (
        previous_submission_status.lower()
        if isinstance(previous_submission_status, str)
        else None
    )

    # This event only republishes a message for static code-upload second-stage
    # evaluation and does not change queue pressure by itself.
    if trigger_source == "submission_message_republished":
        return

    # Debounce status updates: invoke autoscale only when a submission crosses
    # pending/non-pending boundary or reaches terminal states.
    if trigger_source == "submission_status_changed":
        if normalized_status not in pending_statuses.union(terminal_statuses):
            return
        if normalized_previous_status:
            was_pending = normalized_previous_status in pending_statuses
            is_pending = normalized_status in pending_statuses
            if was_pending == is_pending:
                return

    function_name = _resolve_eks_node_autoscale_lambda_function_name()
    if not function_name:
        if not EKS_NODE_AUTOSCALE_LAMBDA_ARN and not os.environ.get(
            "EKS_NODE_AUTOSCALE_LAMBDA_FUNCTION_NAME", ""
        ):
            logger.info(
                "EKS_NODE_AUTOSCALE_LAMBDA_ARN not configured. "
                "Skipping autoscale invoke for challenge %s.",
                challenge_pk,
            )
        return

    payload = {
        "challenge_pk": challenge_pk,
        "trigger_source": trigger_source,
    }
    if submission_pk is not None:
        payload["submission_pk"] = submission_pk
    if submission_status is not None:
        payload["submission_status"] = normalized_status
    if previous_submission_status is not None:
        payload["previous_submission_status"] = normalized_previous_status

    try:
        lambda_client = get_boto3_client("lambda", aws_keys)
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",
            Payload=json.dumps(payload).encode("utf-8"),
        )
    except (ClientError, BotoCoreError) as err:
        logger.exception(
            "Failed to invoke autoscale Lambda for challenge %s: %s",
            challenge_pk,
            err,
        )


def client_token_generator(challenge_pk):
    """
    Returns a 32 characters long client token to
    ensure idempotency with create_service boto3 requests.

    Parameters: None

    Returns:
    str: string of size 32 composed of digits and letters
    """
    remaining_chars = 32 - len(str(challenge_pk))
    random_char_string = "".join(
        random.choices(string.ascii_letters + string.digits, k=remaining_chars)
    )
    client_token = f"{str(challenge_pk)}{random_char_string}"

    return client_token


def register_task_def_by_challenge_pk(client, queue_name, challenge):
    """
    Registers the task definition of the worker for a challenge,
    before creating a service.

    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    queue_name (str):
        queue_name is the queue field of the Challenge model used
        in many parameters of the task def.
    challenge (<class 'challenges.models.Challenge'>):
        The challenge object for whom the task definition is being registered.

    Returns:
    dict: A dict of the task definition and its ARN if successful,
        and an error dictionary if not
    """
    execution_role_arn = COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"]

    if not execution_role_arn:
        message = (
            "Please ensure that the "
            "TASK_EXECUTION_ROLE_ARN is appropriately passed as an environment varible."
        )
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

    if challenge.task_def_arn:
        message = f"Error. Task definition already registered for challenge {challenge.pk}."
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

    ensure_challenge_worker_python_version(challenge)

    definition, error_response = build_task_definition_dict(
        challenge, queue_name
    )
    if error_response:
        return error_response

    try:
        response = client.register_task_definition(**definition)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            task_def_arn = response["taskDefinition"]["taskDefinitionArn"]
            challenge.task_def_arn = task_def_arn
            challenge.save()
        return response
    except ClientError as e:
        logger.exception(e)
        return e.response


def refresh_task_definition_for_challenge(
    challenge, commit_id=None, force_redeploy=True, client=None
):
    """
    Re-register the ECS task definition for a challenge with updated images.

    Deregisters the previous task definition revision after registering a new one,
    and optionally forces the ECS service to redeploy.
    """
    if challenge.uses_ec2_worker or challenge.remote_evaluation:
        return {
            "skipped": True,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }

    if not challenge.task_def_arn:
        message = (
            f"Error. No active task definition registered for challenge "
            f"{challenge.pk}."
        )
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

    if client is None:
        client = get_boto3_client("ecs", aws_keys)

    previous_task_def_arn = challenge.task_def_arn

    image_settings = get_image_settings_for_challenge(challenge, commit_id)
    definition, error_response = build_task_definition_dict(
        challenge, challenge.queue, image_settings=image_settings
    )
    if error_response:
        return error_response

    try:
        response = client.register_task_definition(**definition)
        if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
            return response

        task_def_arn = response["taskDefinition"]["taskDefinitionArn"]
        challenge.task_def_arn = task_def_arn
        update_fields = ["task_def_arn"]
        resolved_worker_image = image_settings["WORKER_IMAGE"]
        if (
            challenge.worker_image_url
            and is_evalai_managed_submission_worker_image(
                challenge.worker_image_url
            )
        ):
            if challenge.worker_image_url != resolved_worker_image:
                challenge.worker_image_url = resolved_worker_image
                update_fields.append("worker_image_url")
        challenge.save(update_fields=update_fields)

        try:
            deregister_response = client.deregister_task_definition(
                taskDefinition=previous_task_def_arn
            )
            if (
                deregister_response["ResponseMetadata"]["HTTPStatusCode"]
                != HTTPStatus.OK
            ):
                logger.warning(
                    "Failed to deregister old task definition %s: %s",
                    previous_task_def_arn,
                    deregister_response,
                )
        except ClientError as e:
            logger.warning(
                "Failed to deregister old task definition %s: %s",
                previous_task_def_arn,
                e,
            )

        if force_redeploy and challenge.workers and challenge.workers > 0:
            return service_manager(
                client,
                challenge,
                num_of_tasks=challenge.workers,
                force_new_deployment=True,
            )
        return response
    except ClientError as e:
        logger.exception(e)
        return e.response


def refresh_worker_task_definitions(
    queryset=None, commit_id=None, dry_run=False
):
    """
    Refresh ECS task definitions for active Fargate-managed challenges.
    """
    from django.utils import timezone

    from .models import Challenge

    if queryset is None:
        queryset = Challenge.objects.filter(
            approved_by_admin=True,
            task_def_arn__isnull=False,
            uses_ec2_worker=False,
            remote_evaluation=False,
            end_date__gt=timezone.now(),
        ).exclude(task_def_arn="")

    if settings.DEBUG:
        failures = []
        for challenge in queryset:
            failures.append(
                {
                    "message": (
                        "Worker task definitions cannot be refreshed on AWS "
                        "ECS in development environment"
                    ),
                    "challenge_pk": challenge.pk,
                }
            )
        return {"count": 0, "failures": failures}

    count = 0
    failures = []

    if dry_run:
        for challenge in queryset:
            count += 1
        return {"count": count, "failures": failures}

    client = get_boto3_client("ecs", aws_keys)

    for challenge in queryset:
        response = refresh_task_definition_for_challenge(
            challenge, commit_id=commit_id, client=client
        )
        if response.get("skipped"):
            continue

        if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
            failures.append(
                {
                    "message": response.get(
                        "Error", "Failed to refresh worker task definition."
                    ),
                    "challenge_pk": challenge.pk,
                }
            )
            continue
        count += 1

    return {"count": count, "failures": failures}


def create_service_by_challenge_pk(client, challenge, client_token):
    """
    Creates the worker service for a challenge, and sets the number of workers to one.

    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>):
        The challenge object  for whom the task definition is being registered.
    client_token (str): The client token generated by client_token_generator()

    Returns:
    dict: The response returned by the create_service method from boto3.
        If unsuccesful, returns an error dictionary
    """

    queue_name = challenge.queue
    service_name = get_ecs_service_name(queue_name)
    if (
        challenge.workers is None
    ):  # Verify if the challenge is new (i.e, service not yet created.).
        if challenge.task_def_arn == "" or challenge.task_def_arn is None:
            response = register_task_def_by_challenge_pk(
                client, queue_name, challenge
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                return response
        task_def_arn = challenge.task_def_arn
        if getattr(challenge, "use_fargate_spot", False):
            definition = {
                "cluster": COMMON_SETTINGS_DICT["CLUSTER"],
                "serviceName": service_name,
                "taskDefinition": task_def_arn,
                "desiredCount": 1,
                "clientToken": client_token,
                "platformVersion": "LATEST",
                "capacityProviderStrategy": get_capacity_provider_strategy(
                    challenge
                ),
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": [
                            VPC_DICT["SUBNET_1"],
                            VPC_DICT["SUBNET_2"],
                        ],
                        "securityGroups": [VPC_DICT["SUBNET_SECURITY_GROUP"]],
                        "assignPublicIp": "ENABLED",
                    }
                },
                "schedulingStrategy": "REPLICA",
                "deploymentController": {"type": "ECS"},
                "deploymentConfiguration": {
                    "deploymentCircuitBreaker": {
                        "enable": True,
                        "rollback": False,
                    }
                },
                "tags": [
                    {"key": "challenge_pk", "value": str(challenge.pk)},
                    {"key": "managed_by", "value": "evalai"},
                ],
                "propagateTags": "SERVICE",
            }
        else:
            definition = service_definition.format(
                CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
                service_name=service_name,
                task_def_arn=task_def_arn,
                client_token=client_token,
                challenge_pk=str(challenge.pk),
                **VPC_DICT,
            )
            definition = load_aws_api_kwargs(definition)
        try:
            response = client.create_service(**definition)
            if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
                challenge.workers = 1
                challenge.save()
                # Set up auto-scaling and schedule cleanup
                setup_auto_scaling_for_service(challenge)
                schedule_challenge_cleanup(challenge)
            return response
        except ClientError as e:
            logger.exception(e)
            return e.response
    else:
        message = (
            f"Worker service for challenge {challenge.pk} already exists. "
            "Please scale, stop or delete."
        )
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }


def _is_inactive_task_definition_error(error):
    """Return True when ECS rejects an update due to a deregistered task definition."""
    if isinstance(error, ClientError):
        error_response = error.response
    else:
        error_response = error
    error_code = error_response.get("Error", {}).get("Code")
    error_message = error_response.get("Error", {}).get("Message", "")
    return error_code == "ClientException" and (
        "TaskDefinition is inactive" in error_message
    )


def _get_ecs_service_task_definition_arn(client, service_name):
    """Return the task definition ARN currently attached to an ECS service."""
    response = client.describe_services(
        cluster=COMMON_SETTINGS_DICT["CLUSTER"],
        services=[service_name],
    )
    services = response.get("services", [])
    if not services:
        return None
    service = services[0]
    if service.get("status") == "INACTIVE":
        return None
    return service.get("taskDefinition")


def _sync_challenge_task_def_from_service(client, challenge, service_name):
    """
    Align challenge.task_def_arn with the ECS service's active task definition.

    Returns True when the challenge record was updated.
    """
    try:
        service_task_def_arn = _get_ecs_service_task_definition_arn(
            client, service_name
        )
    except ClientError as e:
        logger.warning(
            "Failed to fetch active task definition for service %s: %s",
            service_name,
            e,
        )
        return False
    if not service_task_def_arn:
        return False
    if challenge.task_def_arn == service_task_def_arn:
        return False
    logger.warning(
        "Syncing stale task_def_arn for challenge %s from %s to %s",
        challenge.pk,
        challenge.task_def_arn,
        service_task_def_arn,
    )
    challenge.task_def_arn = service_task_def_arn
    challenge.save(update_fields=["task_def_arn"])
    return True


def _build_update_service_kwargs(
    service_name, task_def_arn, num_of_tasks, force_new_deployment
):
    kwargs = update_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        task_def_arn=task_def_arn,
        force_new_deployment=force_new_deployment,
        num_of_tasks=num_of_tasks,
    )
    return load_aws_api_kwargs(kwargs)


def update_service_by_challenge_pk(
    client, challenge, num_of_tasks, force_new_deployment=False
):
    """
    Updates the worker service for a challenge, and scales the number of workers to num_of_tasks.

    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>): The challenge object  for whom the task definition is being registered.
    num_of_tasks (int): Number of workers to scale to for the challenge.
    force_new_deployment (bool): Set True (mainly for restarting) to force ECS to
        redeploy tasks using the current task definition revision. This does not
        change the container image unless the task definition was updated.

    Returns:
    dict: The response returned by the update_service method from boto3. If unsuccesful, returns an error dictionary
    """

    queue_name = challenge.queue
    service_name = get_ecs_service_name(queue_name)
    task_def_arn = challenge.task_def_arn

    if force_new_deployment:
        kwargs = _build_update_service_kwargs(
            service_name, task_def_arn, num_of_tasks, force_new_deployment
        )
    else:
        # Scale/stop without sending taskDefinition so stale DB ARNs do not
        # block worker management when the ECS service still has an active one.
        kwargs = scale_service_args.format(
            CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
            service_name=service_name,
            num_of_tasks=num_of_tasks,
        )
        kwargs = load_aws_api_kwargs(kwargs)

    try:
        response = client.update_service(**kwargs)
    except ClientError as e:
        if force_new_deployment and _is_inactive_task_definition_error(e):
            if _sync_challenge_task_def_from_service(
                client, challenge, service_name
            ):
                kwargs = _build_update_service_kwargs(
                    service_name,
                    challenge.task_def_arn,
                    num_of_tasks,
                    force_new_deployment,
                )
                try:
                    response = client.update_service(**kwargs)
                    if (
                        response["ResponseMetadata"]["HTTPStatusCode"]
                        == HTTPStatus.OK
                    ):
                        challenge.workers = num_of_tasks
                        challenge.save()
                    return response
                except ClientError as retry_error:
                    logger.exception(retry_error)
                    return retry_error.response
        logger.exception(e)
        return e.response

    if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
        challenge.workers = num_of_tasks
        challenge.save()
        if not force_new_deployment:
            _sync_challenge_task_def_from_service(
                client, challenge, service_name
            )
    return response


def delete_service_by_challenge_pk(challenge):
    """
    Deletes the workers service of a challenge.

    Before deleting, it scales down the number of workers in the service to 0,
    then proceeds to delete the service.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>):
        The challenge object for whom the task definition is being registered.

    Returns:
    dict: The response returned by the delete_service method from boto3
    """
    client = get_boto3_client("ecs", aws_keys)
    queue_name = challenge.queue
    service_name = get_ecs_service_name(queue_name)
    kwargs = delete_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        force=True,
    )
    kwargs = load_aws_api_kwargs(kwargs)
    try:
        # Clean up auto-scaling and EventBridge schedule before deleting
        cleanup_auto_scaling_for_service(challenge)

        if challenge.workers != 0:
            response = update_service_by_challenge_pk(
                client, challenge, 0, False
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                # If service doesn't exist, proceed to delete anyway (will be
                # handled gracefully)
                error_code = response.get("Error", {}).get("Code")
                if error_code != "ServiceNotFoundException":
                    return response

        response = client.delete_service(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = None
            challenge.save()
            if challenge.task_def_arn:
                try:
                    client.deregister_task_definition(
                        taskDefinition=challenge.task_def_arn
                    )
                except ClientError as deregister_error:
                    if not _is_inactive_task_definition_error(
                        deregister_error
                    ):
                        logger.exception(deregister_error)
                        return deregister_error.response
                    logger.warning(
                        "Task definition %s for challenge %s was already "
                        "inactive; treating deregistration as successful",
                        challenge.task_def_arn,
                        challenge.pk,
                    )
            challenge.task_def_arn = ""
            challenge.save()
        return response
    except ClientError as e:
        # Handle ServiceNotFoundException gracefully - if the service doesn't exist,
        # the deletion goal is achieved. Clean up challenge state and return
        # success.
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ServiceNotFoundException":
            logger.info(
                "Service for challenge %s does not exist, treating delete as success",
                challenge.pk,
            )
            challenge.workers = None
            challenge.save()
            # Try to deregister task definition if it exists, but don't fail if
            # it doesn't
            if challenge.task_def_arn:
                try:
                    client.deregister_task_definition(
                        taskDefinition=challenge.task_def_arn
                    )
                except ClientError:
                    pass  # Task definition may not exist either
            challenge.task_def_arn = ""
            challenge.save()
            # Return a success-like response
            return {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
        logger.exception(e)
        return e.response


def service_manager(
    client, challenge, num_of_tasks=None, force_new_deployment=False
):
    """
    This method determines if the challenge is new or not,
    and accordingly calls <update or create>_by_challenge_pk.

    Called by: Start, Stop & Scale methods for multiple workers.

    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    challenge (<class 'challenges.models.Challenge'>):
        The challenge object for whom the task definition is being registered.
    num_of_tasks: The number of workers to scale to (relevant only if the challenge is not new).
                  default: None

    Returns:
    dict: The response returned by the respective functions
        update_service_by_challenge_pk or create_service_by_challenge_pk
    """
    if challenge.workers is not None:
        response = update_service_by_challenge_pk(
            client, challenge, num_of_tasks, force_new_deployment
        )
        # Handle ServiceNotFoundException: ECS service was deleted (e.g. after
        # AWS key rotation) but DB still has workers set. Sync state and
        # either create the service (start/restart) or treat stop as success.
        error_code = response.get("Error", {}).get("Code")
        if error_code == "ServiceNotFoundException":
            if num_of_tasks == 0:
                challenge.workers = 0
                challenge.save()
                return {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
            # num_of_tasks > 0: create the service
            challenge.workers = None
            challenge.save()
            client_token = client_token_generator(challenge.pk)
            return create_service_by_challenge_pk(
                client, challenge, client_token
            )
        return response
    else:
        client_token = client_token_generator(challenge.pk)
        response = create_service_by_challenge_pk(
            client, challenge, client_token
        )
        return response


def stop_ec2_instance(challenge):
    """
    Stop the EC2 instance associated with a challenge if status checks are ready.

    Args:
        challenge (Challenge): The challenge for which the EC2 instance needs to be stopped.

    Returns:
        dict: A dictionary containing the status and message of the stop operation.
    """
    target_instance_id = challenge.ec2_instance_id

    ec2 = get_boto3_client("ec2", aws_keys)
    status_response = ec2.describe_instance_status(
        InstanceIds=[target_instance_id]
    )

    if status_response["InstanceStatuses"]:
        instance_status = status_response["InstanceStatuses"][0]
        system_status = instance_status["SystemStatus"]["Status"]
        instance_status_check = instance_status["InstanceStatus"]["Status"]

        if system_status == "ok" and instance_status_check == "ok":
            instance_state = instance_status["InstanceState"]["Name"]

            if instance_state == "running":
                try:
                    response = ec2.stop_instances(
                        InstanceIds=[target_instance_id]
                    )
                    message = f"Instance for challenge {challenge.pk} successfully stopped."
                    return {
                        "response": response,
                        "message": message,
                    }
                except ClientError as e:
                    logger.exception(e)
                    return {
                        "error": e.response,
                    }
            else:
                message = (
                    f"Instance for challenge {challenge.pk} is not running. "
                    "Please ensure the instance is running."
                )
                return {
                    "error": message,
                }
        else:
            message = (
                f"Instance status checks are not ready for challenge {challenge.pk}. "
                "Please wait for the status checks to pass."
            )
            return {
                "error": message,
            }
    else:
        message = (
            f"Instance for challenge {challenge.pk} not found. "
            "Please ensure the instance exists."
        )
        return {
            "error": message,
        }


def describe_ec2_instance(challenge):
    """
    Describe the EC2 instance associated with a challenge.

    Args:
        challenge (Challenge): The challenge for which the EC2 instance description is needed.

    Returns:
        dict: A dictionary containing the status and message of the operation.
    """
    target_instance_id = challenge.ec2_instance_id
    try:
        ec2 = get_boto3_client("ec2", aws_keys)
        response = ec2.describe_instances(InstanceIds=[target_instance_id])

        instances = [
            instance
            for reservation in response["Reservations"]
            for instance in reservation["Instances"]
        ]
        instance = instances[0]
        return {"message": instance}
    except Exception as e:
        logger.exception(e)
        return {
            "error": e.response,
        }


def start_ec2_instance(challenge):
    """
    Start the EC2 instance associated with a challenge.

    Args:
        challenge (Challenge): The challenge for which the EC2 instance needs to be started.

    Returns:
        dict: A dictionary containing the status and message of the start operation.
    """

    target_instance_id = challenge.ec2_instance_id

    ec2 = get_boto3_client("ec2", aws_keys)
    response = ec2.describe_instances(InstanceIds=[target_instance_id])

    instances = [
        instance
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]

    if instances:
        instance = instances[0]
        instance_id = instance["InstanceId"]
        if instance["State"]["Name"] == "stopped":
            try:
                response = ec2.start_instances(InstanceIds=[instance_id])
                message = f"Instance for challenge {challenge.pk} successfully started."
                return {
                    "response": response,
                    "message": message,
                }
            except ClientError as e:
                logger.exception(e)
                return {
                    "error": e.response,
                }
        else:
            message = (
                f"Instance for challenge {challenge.pk} is running. "
                "Please ensure the instance is stopped."
            )
            return {
                "error": message,
            }
    else:
        message = (
            f"Instance for challenge {challenge.pk} not found. "
            "Please ensure the instance exists."
        )
        return {
            "error": message,
        }


def restart_ec2_instance(challenge):
    """
    Reboot the EC2 instance associated with a challenge.

    Args:
        challenge (Challenge): The challenge for which the EC2 instance needs to be restarted.

    Returns:
        dict: A dictionary containing the status and message of the reboot operation.
    """

    target_instance_id = challenge.ec2_instance_id

    ec2 = get_boto3_client("ec2", aws_keys)

    try:
        response = ec2.reboot_instances(InstanceIds=[target_instance_id])
        message = (
            f"Instance for challenge {challenge.pk} successfully restarted."
        )
        return {
            "response": response,
            "message": message,
        }
    except ClientError as e:
        logger.exception(e)
        return {
            "error": e.response,
        }


def terminate_ec2_instance(challenge):
    """
    Terminate the EC2 instance associated with a challenge.

    Args:
        challenge (Challenge): The challenge for which the EC2 instance needs to be terminated.

    Returns:
        dict: A dictionary containing the status and message of the terminated operation.
    """

    target_instance_id = challenge.ec2_instance_id

    ec2 = get_boto3_client("ec2", aws_keys)

    try:
        response = ec2.terminate_instances(InstanceIds=[target_instance_id])
        challenge.ec2_instance_id = ""
        challenge.save()
        message = (
            f"Instance for challenge {challenge.pk} successfully terminated."
        )
        return {
            "response": response,
            "message": message,
        }
    except ClientError as e:
        logger.exception(e)
        return {
            "error": e.response,
        }


def create_ec2_instance(
    challenge,
    ec2_storage=None,
    worker_instance_type=None,
    worker_image_url=None,
):
    """
    Create the EC2 instance associated with a challenge.

    Args:
        challenge (Challenge): The challenge for which the EC2 instance needs to be created.

    Returns:
        dict: A dictionary containing the status and message of the creation operation.
    """

    target_instance_id = challenge.ec2_instance_id
    if target_instance_id:
        return {
            "error": f"Challenge {challenge.pk} has existing EC2 instance ID. "
            "Please ensure there is no existing associated instance before trying to create one."
        }

    ec2 = get_boto3_client("ec2", aws_keys)

    with open("/code/scripts/deployment/deploy_ec2_worker.sh") as f:
        ec2_worker_script = f.read()

    if ec2_storage:
        challenge.ec2_storage = ec2_storage

    if worker_instance_type:
        challenge.worker_instance_type = worker_instance_type

    if worker_image_url:
        challenge.worker_image_url = worker_image_url
    else:
        challenge.worker_image_url = (
            ""
            if challenge.worker_image_url is None
            else challenge.worker_image_url
        )

    worker_python_version = ensure_challenge_worker_python_version(challenge)

    variables = {
        "AWS_ACCOUNT_ID": aws_keys["AWS_ACCOUNT_ID"],
        "AWS_ACCESS_KEY_ID": aws_keys["AWS_ACCESS_KEY_ID"],
        "AWS_SECRET_ACCESS_KEY": aws_keys["AWS_SECRET_ACCESS_KEY"],
        "AWS_REGION": aws_keys["AWS_REGION"],
        "PK": str(challenge.pk),
        "QUEUE": challenge.queue,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "CUSTOM_WORKER_IMAGE": challenge.worker_image_url,
        "WORKER_PYTHON_VERSION": worker_python_version,
    }

    for key, value in variables.items():
        ec2_worker_script = ec2_worker_script.replace("${" + key + "}", value)

    instance_name = f"Worker-Instance-{settings.ENVIRONMENT}-{challenge.pk}"
    blockDeviceMappings = [
        {
            "DeviceName": "/dev/sda1",
            "Ebs": {
                "DeleteOnTermination": True,
                "VolumeSize": challenge.ec2_storage,  # TODO: Make this customizable
                "VolumeType": "gp2",
            },
        },
    ]

    try:
        response = ec2.run_instances(
            BlockDeviceMappings=blockDeviceMappings,
            ImageId="ami-0747bdcabd34c712a",  # TODO: Make this customizable
            InstanceType=challenge.worker_instance_type,
            MinCount=1,
            MaxCount=1,
            SubnetId=VPC_DICT["SUBNET_1"],
            KeyName="cloudcv_2016",  # TODO: Remove hardcoding
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": instance_name},
                    ],
                }
            ],
            UserData=ec2_worker_script,
        )
        challenge.uses_ec2_worker = True
        challenge.ec2_instance_id = response["Instances"][0]["InstanceId"]
        challenge.save()
        message = (
            f"Instance for challenge {challenge.pk} successfully created."
        )
        return {
            "response": response,
            "message": message,
        }
    except ClientError as e:
        logger.exception(e)
        return {
            "error": e.response,
        }


def update_sqs_retention_period(challenge):
    """
    Update the SQS retention period for a challenge.

    Args:
        challenge (Challenge): The challenge for which the SQS retention period is to be updated.

    Returns:
        dict: A dictionary containing the status and message of the operation.
    """
    sqs_retention_period = str(challenge.sqs_retention_period)
    try:
        sqs = get_boto3_client("sqs", aws_keys)
        queue_url = sqs.get_queue_url(QueueName=challenge.queue)["QueueUrl"]
        response = sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={"MessageRetentionPeriod": sqs_retention_period},
        )
        return {"message": response}
    except Exception as e:
        logger.exception(e)
        return {
            "error": str(e),
        }


def start_workers(queryset):
    """
    The function called by the admin action method to start all the selected workers.

    Calls the service_manager method. Before calling, checks if all the workers are incactive.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    if settings.DEBUG:
        failures = []
        for challenge in queryset:
            failures.append(
                {
                    "message": "Workers cannot be started on AWS ECS service in development environment",
                    "challenge_pk": challenge.pk,
                }
            )
        return {"count": 0, "failures": failures}

    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if (challenge.workers == 0) or (challenge.workers is None):
            response = service_manager(
                client, challenge=challenge, num_of_tasks=1
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response["Error"],
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            # Clear any OOM or evaluation module error on successful start
            if challenge.evaluation_module_error:
                challenge.evaluation_module_error = None
                challenge.save()
            count += 1
        else:
            response = "Please select challenge with inactive workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}


def stop_workers(queryset):
    """
    The function called by the admin action method to stop all the selected workers.

    Calls the service_manager method. Before calling, verifies that the challenge is not new, and is active.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    if settings.DEBUG:
        failures = []
        for challenge in queryset:
            failures.append(
                {
                    "message": "Workers cannot be stopped on AWS ECS service in development environment",
                    "challenge_pk": challenge.pk,
                }
            )
        return {"count": 0, "failures": failures}

    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(
                client, challenge=challenge, num_of_tasks=0
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response["Error"],
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            count += 1
        else:
            response = "Please select challenges with active workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}


def scale_workers(queryset, num_of_tasks):
    """
    The function called by the admin action method to scale all the selected workers.

    Calls the service_manager method. Before calling, checks if the target scaling number is different than current.

    Scaling to a non-zero count also moves the Application Auto Scaling ceiling
    to match. The scale-up policy uses ExactCapacity, so leaving a stale ceiling
    behind would let the next queue-depth alarm override the requested count in
    whichever direction the ceiling disagrees.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    if settings.DEBUG:
        failures = []
        for challenge in queryset:
            failures.append(
                {
                    "message": "Workers cannot be scaled on AWS ECS service in development environment",
                    "challenge_pk": challenge.pk,
                }
            )
        return {"count": 0, "failures": failures}

    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if challenge.workers is None:
            response = "Please start worker(s) before scaling."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
            continue
        if num_of_tasks == challenge.workers:
            response = f"Please scale to a different number. Challenge has {num_of_tasks} worker(s)."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
            continue
        # Move the auto-scaling ceiling before ECS. Scaling up past a stale
        # ceiling gets clamped back down; scaling down below one gets pushed
        # back up, since the scale-up policy restores ExactCapacity == ceiling.
        # A target of 0 is an idle pause, not a request to change the ceiling.
        ceiling_changed = False
        previous_max_ecs_workers = challenge.max_ecs_workers
        if num_of_tasks > 0 and num_of_tasks != challenge.max_ecs_workers:
            challenge.max_ecs_workers = num_of_tasks
            if not setup_auto_scaling_for_service(challenge):
                challenge.max_ecs_workers = previous_max_ecs_workers
                failures.append(
                    {
                        "message": "Failed to update auto-scaling configuration. Workers were not scaled.",
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            ceiling_changed = True
        response = service_manager(
            client, challenge=challenge, num_of_tasks=num_of_tasks
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
            if ceiling_changed:
                challenge.max_ecs_workers = previous_max_ecs_workers
                if not setup_auto_scaling_for_service(challenge):
                    logger.error(
                        "Failed to restore auto-scaling ceiling for "
                        "challenge %s; AWS bounds may be inconsistent.",
                        challenge.pk,
                    )
            failures.append(
                {"message": response["Error"], "challenge_pk": challenge.pk}
            )
            continue
        if ceiling_changed:
            challenge.save(update_fields=["max_ecs_workers"])
        count += 1
    return {"count": count, "failures": failures}


def scale_resources(challenge, worker_cpu_cores, worker_memory):
    """
    The function called by scale_resources_by_challenge_pk to send the AWS ECS request to update the resources used by
    a challenge's workers.

    Registers a new task definition with updated resources and deregisters the
    previous task definition after the new revision is saved.

    Parameters:
    challenge (): The challenge object for whom the task definition is being registered.
    worker_cpu_cores (int): vCPU (1 CPU core = 1024 vCPU) that should be assigned to workers.
    worker_memory (int): The amount of memory (MB) that should be assigned to each worker.

    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """

    client = get_boto3_client("ecs", aws_keys)

    if (
        challenge.worker_cpu_cores == worker_cpu_cores
        and challenge.worker_memory == worker_memory
    ):
        return {
            "Success": True,
            "Message": "Worker not modified",
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }

    if not challenge.task_def_arn:
        message = f"Error. No active task definition registered for the challenge {challenge.pk}."
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

    previous_task_def_arn = challenge.task_def_arn

    image_settings = get_image_settings_for_challenge(challenge)
    task_def, error_response = build_task_definition_dict(
        challenge,
        challenge.queue,
        image_settings=image_settings,
        worker_cpu_cores=worker_cpu_cores,
        worker_memory=worker_memory,
    )
    if error_response:
        return error_response

    try:
        response = client.register_task_definition(**task_def)
        if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
            return response

        challenge.worker_cpu_cores = worker_cpu_cores
        challenge.worker_memory = worker_memory
        task_def_arn = response["taskDefinition"]["taskDefinitionArn"]

        challenge.task_def_arn = task_def_arn
        challenge.save()
        force_new_deployment = False
        service_name = get_ecs_service_name(challenge.queue)
        num_of_tasks = challenge.workers
        kwargs = update_service_args.format(
            CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
            service_name=service_name,
            task_def_arn=task_def_arn,
            num_of_tasks=num_of_tasks,
            force_new_deployment=force_new_deployment,
        )
        kwargs = load_aws_api_kwargs(kwargs)
        response = client.update_service(**kwargs)

        try:
            deregister_response = client.deregister_task_definition(
                taskDefinition=previous_task_def_arn
            )
            if (
                deregister_response["ResponseMetadata"]["HTTPStatusCode"]
                != HTTPStatus.OK
            ):
                logger.warning(
                    "Failed to deregister old task definition %s: %s",
                    previous_task_def_arn,
                    deregister_response,
                )
        except ClientError as e:
            logger.warning(
                "Failed to deregister old task definition %s: %s",
                previous_task_def_arn,
                e,
            )

        return response
    except ClientError as e:
        logger.exception(e)
        return e.response


def delete_workers(queryset):
    """
    The function called by the admin action method to delete all the selected workers.

    Calls the delete_service_by_challenge_pk method. Before calling, verifies that the challenge is not new.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    if settings.DEBUG:
        failures = []
        for challenge in queryset:
            failures.append(
                {
                    "message": "Workers cannot be deleted on AWS ECS service in development environment",
                    "challenge_pk": challenge.pk,
                }
            )
        return {"count": 0, "failures": failures}

    count = 0
    failures = []
    for challenge in queryset:
        if challenge.workers is not None:
            response = delete_service_by_challenge_pk(challenge=challenge)
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response["Error"],
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            count += 1
            log_group_name = get_log_group_name(challenge.pk)
            delete_log_group(log_group_name)
        else:
            response = "Please select challenges with active workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}


def restart_workers(queryset):
    """
    The function called by the admin action method to restart all the selected workers.

    Calls the service_manager method. Before calling, verifies that the challenge worker(s) is(are) active.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    if settings.DEBUG:
        failures = []
        for challenge in queryset:
            failures.append(
                {
                    "message": "Workers cannot be restarted on AWS ECS service in development environment",
                    "challenge_pk": challenge.pk,
                }
            )
        return {"count": 0, "failures": failures}

    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = refresh_task_definition_for_challenge(
                challenge, client=client
            )
            if response.get("skipped"):
                failures.append(
                    {
                        "message": (
                            "Worker task definition refresh is not supported "
                            "for this challenge type."
                        ),
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response.get(
                            "Error", "Failed to restart worker."
                        ),
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            # Clear any OOM or evaluation module error on successful restart
            if challenge.evaluation_module_error:
                challenge.evaluation_module_error = None
                challenge.save()
            count += 1
        else:
            response = "Please select challenges with active workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}


def _file_content_changed(old_field, new_field):
    """Compare two Django FileField values by content hash, not path.

    Returns True if the file content actually changed, False if identical.
    Handles cases where one or both fields are empty/missing.
    """
    if bool(old_field) != bool(new_field):
        return True
    if not old_field and not new_field:
        return False
    try:
        old_field.seek(0)
        old_hash = hashlib.md5(old_field.read()).hexdigest()
        old_field.seek(0)
        new_field.seek(0)
        new_hash = hashlib.md5(new_field.read()).hexdigest()
        new_field.seek(0)
        return old_hash != new_hash
    except Exception:
        return True


def restart_workers_signal_callback(sender, instance, field_name, **kwargs):
    """
    Called when either evaluation_script or test_annotation_script for challenge
    is updated, to restart the challenge workers.
    """
    if settings.DEBUG:
        return

    prev = getattr(instance, f"_original_{field_name}")
    curr = getattr(instance, f"{field_name}")

    if field_name == "evaluation_script":
        instance._original_evaluation_script = curr
    elif field_name == "test_annotation":
        instance._original_test_annotation = curr

    if _file_content_changed(prev, curr):
        challenge = None
        if field_name == "test_annotation":
            challenge = instance.challenge
        else:
            challenge = instance

        response = restart_workers([challenge])

        count, failures = response["count"], response["failures"]

        logger.info(
            f"The worker service for challenge {challenge.pk} was restarted, "
            f"as {field_name} was changed."
        )

        if count != 1:
            logger.warning(
                f"Worker(s) for challenge {challenge.id} couldn't restart! "
                f"Error: {failures[0]['message']}"
            )
        else:
            logger.info(
                "Workers restarted successfully for challenge %s "
                "after %s change.",
                challenge.id,
                field_name,
            )


def get_logs_from_cloudwatch(
    log_group_name, log_stream_prefix, start_time, end_time, pattern, limit
):
    """
    To fetch logs of a container from cloudwatch within a specific time frame.
    """
    client = get_boto3_client("logs", aws_keys)
    logs = []
    if settings.DEBUG:
        logs = [
            "The worker logs in the development environment are available on the terminal. Please use docker-compose logs -f worker to view the logs."
        ]
    else:
        try:
            response = client.filter_log_events(
                logGroupName=log_group_name,
                logStreamNamePrefix=log_stream_prefix,
                startTime=start_time,
                endTime=end_time,
                filterPattern=pattern,
                limit=limit,
            )
            for event in response["events"]:
                logs.append(event["message"])
            nextToken = response.get("nextToken", None)
            while nextToken is not None:
                response = client.filter_log_events(
                    logGroupName=log_group_name,
                    logStreamNamePrefix=log_stream_prefix,
                    startTime=start_time,
                    endTime=end_time,
                    filterPattern=pattern,
                    limit=limit,
                    nextToken=nextToken,
                )
                nextToken = response.get("nextToken", None)
                for event in response["events"]:
                    logs.append(event["message"])
        except Exception as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return logs

            logger.exception(e)
            return [
                f"There is an error in displaying logs. Please find the full error traceback here {e}"
            ]
    return logs


def delete_log_group(log_group_name):
    if settings.DEBUG:
        pass
    else:
        try:
            client = get_boto3_client("logs", aws_keys)
            client.delete_log_group(logGroupName=log_group_name)
        except Exception as e:
            logger.exception(e)


def get_nodegroup_name_for_challenge(challenge_obj):
    """
    Build the deterministic nodegroup name for a challenge.

    The name is derived from the challenge rather than stored, so recreating a
    nodegroup reuses the same name and leaves
    ChallengeEvaluationCluster.nodegroup_name (which autoscaling targets) valid.

    Arguments:
        challenge_obj {<class 'apps.challenges.models.Challenge'>} -- challenge instance
    Returns:
        {str} -- nodegroup name
    """
    environment_suffix = "{}-{}".format(challenge_obj.pk, settings.ENVIRONMENT)
    return "{}-{}-nodegroup".format(
        challenge_obj.title.replace(" ", "-")[:20], environment_suffix
    )


def create_nodegroup_for_challenge(
    client, challenge_obj, cluster_name, nodegroup_name
):
    """
    Issue the create_nodegroup call for a challenge and record the name.

    Shared by initial cluster setup and by recreation after an immutable
    nodegroup field changes, so both paths always send the same argument set.

    Arguments:
        client -- boto3 EKS client authenticated for the challenge
        challenge_obj {<class 'apps.challenges.models.Challenge'>} -- challenge instance
        cluster_name {str} -- name of eks cluster
        nodegroup_name {str} -- name of the nodegroup to create
    Returns:
        {dict or None} -- the create_nodegroup response, or None when the
            nodegroup was not created. A nodegroup that was created but did
            not reach ACTIVE within the waiter's budget still returns the
            response, because it exists and must not be treated as absent.
    """
    from .models import ChallengeEvaluationCluster

    cluster_meta = get_code_upload_setup_meta_for_challenge(challenge_obj.pk)
    try:
        response = client.create_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name,
            scalingConfig={
                "minSize": challenge_obj.min_worker_instance,
                "maxSize": challenge_obj.max_worker_instance,
                "desiredSize": challenge_obj.desired_worker_instance,
            },
            diskSize=challenge_obj.worker_disk_size,
            subnets=[cluster_meta["SUBNET_1"], cluster_meta["SUBNET_2"]],
            instanceTypes=[challenge_obj.worker_instance_type],
            amiType=challenge_obj.worker_ami_type,
            nodeRole=cluster_meta["EKS_NODEGROUP_ROLE_ARN"],
        )
        logger.info("Nodegroup create: {}".format(response))
    except ClientError as e:
        logger.exception(e)
        return None

    # Record the name so autoscaling targets this nodegroup explicitly.
    try:
        ChallengeEvaluationCluster.objects.filter(
            challenge_id=challenge_obj.pk
        ).update(nodegroup_name=nodegroup_name)
    except DatabaseError as e:
        logger.exception(e)

    try:
        waiter = client.get_waiter("nodegroup_active")
        waiter.wait(clusterName=cluster_name, nodegroupName=nodegroup_name)
    except (ClientError, BotoCoreError) as e:
        # WaiterError is a BotoCoreError. Letting it escape would skip the
        # caller's error handling entirely; returning None would be worse
        # still, since the nodegroup does exist and the caller would report it
        # as missing and may delete it on the next attempt.
        logger.exception(e)
        logger.warning(
            "Nodegroup %s for challenge %s was created but has not reached "
            "ACTIVE yet. Treating it as created.",
            nodegroup_name,
            challenge_obj.pk,
        )

    return response


@app.task
def create_eks_nodegroup(challenge, cluster_name):
    """
    Creates a nodegroup when a EKS cluster is created by the EvalAI admin
    Arguments:
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
        cluster_name {str} -- name of eks cluster
    """
    from .models import Challenge
    from .utils import get_aws_credentials_for_challenge

    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object

    # The serialized challenge is a snapshot taken when approved_by_admin
    # flipped, and cluster setup takes many minutes. Re-read the worker
    # configuration so an edit made in that window is not silently dropped:
    # the post_save hook cannot recreate a nodegroup that does not exist yet,
    # so this is the only place that edit can still be applied.
    try:
        challenge_obj = Challenge.objects.get(pk=challenge_obj.pk)
    except (Challenge.DoesNotExist, DatabaseError) as e:
        logger.exception(e)

    nodegroup_name = get_nodegroup_name_for_challenge(challenge_obj)
    challenge_aws_keys = get_aws_credentials_for_challenge(challenge_obj.pk)
    client = get_boto3_client("eks", challenge_aws_keys)
    response = create_nodegroup_for_challenge(
        client, challenge_obj, cluster_name, nodegroup_name
    )
    if response is None:
        return

    construct_and_send_eks_cluster_creation_mail(challenge_obj)
    # starting the code-upload-worker
    client = get_boto3_client("ecs", aws_keys)
    client_token = client_token_generator(challenge_obj.pk)
    create_service_by_challenge_pk(client, challenge_obj, client_token)


def validate_eks_nodegroup_config(challenge_obj, eks_client, cluster_name):
    """
    Check a challenge's nodegroup configuration before it is applied to AWS.

    Recreating a nodegroup deletes the existing one first, so an invalid
    configuration would leave the challenge with no capacity at all. Every
    problem that can be detected up front is detected here instead.

    Arguments:
        challenge_obj {<class 'apps.challenges.models.Challenge'>} -- challenge instance
        eks_client -- boto3 EKS client authenticated for the challenge
        cluster_name {str} -- name of eks cluster
    Returns:
        {list} -- human readable problems, empty when the config is usable
    """
    from .utils import get_aws_credentials_for_challenge

    errors = []

    instance_type = challenge_obj.worker_instance_type
    if not instance_type:
        errors.append("worker_instance_type is empty.")
    else:
        try:
            ec2_client = get_boto3_client(
                "ec2", get_aws_credentials_for_challenge(challenge_obj.pk)
            )
            offerings = ec2_client.describe_instance_type_offerings(
                LocationType="region",
                Filters=[{"Name": "instance-type", "Values": [instance_type]}],
            )
            if not offerings.get("InstanceTypeOfferings"):
                errors.append(
                    "Instance type {} is not offered in this region.".format(
                        instance_type
                    )
                )
        except (ClientError, BotoCoreError) as e:
            logger.exception(e)
            errors.append(
                "Could not verify instance type {}: {}".format(
                    instance_type, e
                )
            )

    ami_type = challenge_obj.worker_ami_type
    if ami_type not in settings.EKS_SUPPORTED_AMI_TYPES:
        errors.append("Unknown worker_ami_type {}.".format(ami_type))
    else:
        if (
            not challenge_obj.cpu_only_jobs
            and ami_type not in settings.EKS_GPU_AMI_TYPES
        ):
            errors.append(
                "AMI type {} has no GPU driver, but cpu_only_jobs is "
                "disabled.".format(ami_type)
            )
        try:
            cluster_version = eks_client.describe_cluster(name=cluster_name)[
                "cluster"
            ]["version"]
            if ami_type.startswith("AL2_") and _version_at_least(
                cluster_version, settings.EKS_AL2_REMOVED_IN_VERSION
            ):
                errors.append(
                    "AMI type {} is not available on Kubernetes {}. Use an "
                    "AL2023 or Bottlerocket AMI type.".format(
                        ami_type, cluster_version
                    )
                )
        except (ClientError, BotoCoreError, KeyError) as e:
            logger.exception(e)
            errors.append("Could not read cluster version: {}".format(e))

    disk_size = challenge_obj.worker_disk_size
    if not isinstance(disk_size, int) or disk_size <= 0:
        errors.append("worker_disk_size must be a positive integer.")

    errors.extend(_validate_nodegroup_scaling(challenge_obj))

    return errors


def _validate_nodegroup_scaling(challenge_obj):
    """
    Check the scaling bounds CreateNodegroup will be given.

    All three fields are nullable on the model and nothing stops an admin
    saving a minimum above the maximum. Left unchecked, an invalid combination
    passes validation, the live nodegroup is deleted, and only then does
    CreateNodegroup reject it, leaving the challenge with no workers at all.

    Arguments:
        challenge_obj {<class 'apps.challenges.models.Challenge'>} -- challenge instance
    Returns:
        {list} -- human readable problems, empty when the bounds are usable
    """
    errors = []
    bounds = {}
    for field in settings.EKS_NODEGROUP_SCALING_FIELDS:
        value = getattr(challenge_obj, field)
        # bool is an int subclass, and True would silently become 1.
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append("{} must be a non-negative integer.".format(field))
        else:
            bounds[field] = value

    if len(bounds) != len(settings.EKS_NODEGROUP_SCALING_FIELDS):
        return errors

    min_size = bounds["min_worker_instance"]
    max_size = bounds["max_worker_instance"]
    desired_size = bounds["desired_worker_instance"]

    if max_size < 1:
        errors.append("max_worker_instance must be at least 1.")
    if min_size > max_size:
        errors.append(
            "min_worker_instance ({}) cannot exceed max_worker_instance "
            "({}).".format(min_size, max_size)
        )
    if not min_size <= desired_size <= max_size:
        errors.append(
            "desired_worker_instance ({}) must be between "
            "min_worker_instance ({}) and max_worker_instance ({}).".format(
                desired_size, min_size, max_size
            )
        )

    return errors


def _version_at_least(version, minimum):
    """
    Compare two dotted Kubernetes version strings.

    Arguments:
        version {str} -- version reported by EKS, e.g. "1.36"
        minimum {str} -- version to compare against, e.g. "1.33"
    Returns:
        {bool} -- True when version >= minimum, False when unparseable
    """
    try:
        parsed = tuple(int(part) for part in str(version).split(".")[:2])
        floor = tuple(int(part) for part in str(minimum).split(".")[:2])
    except (TypeError, ValueError):
        return False
    return parsed >= floor


def _get_challenge_cluster(challenge_pk):
    """
    Resolve the challenge and its evaluation cluster for a sync task.

    Arguments:
        challenge_pk {int} -- challenge primary key
    Returns:
        {tuple} -- (challenge, cluster), or (None, None) when the challenge
            has no evaluation cluster
    """
    from .models import ChallengeEvaluationCluster

    try:
        cluster = ChallengeEvaluationCluster.objects.select_related(
            "challenge"
        ).get(challenge_id=challenge_pk)
    except ChallengeEvaluationCluster.DoesNotExist:
        logger.info(
            "Challenge %s has no evaluation cluster yet. Skipping nodegroup "
            "sync.",
            challenge_pk,
        )
        return None, None
    except DatabaseError as e:
        logger.exception(e)
        return None, None

    return cluster.challenge, cluster


def _resolve_nodegroup_name(client, challenge_pk, cluster):
    """
    Find the name of a challenge's live nodegroup.

    nodegroup_name is nullable and was only added recently, so clusters
    provisioned before then have none recorded. The name cannot be re-derived
    from the challenge, because it embeds the title as it was at creation time:
    a renamed challenge would derive a name that matches nothing, delete
    nothing, and then create a second nodegroup alongside the live one.
    Ask AWS instead.

    Arguments:
        client -- boto3 EKS client authenticated for the challenge
        challenge_pk {int} -- challenge primary key
        cluster {<class 'apps.challenges.models.ChallengeEvaluationCluster'>}
    Returns:
        {str or None} -- nodegroup name, or None when it cannot be pinned down
    """
    from .models import ChallengeEvaluationCluster

    if cluster.nodegroup_name:
        # A recorded name can still be wrong: the nodegroup may have been
        # replaced by hand under a different name. Trusting it blindly would
        # make every sync fail on describe_nodegroup until someone edited the
        # database, so confirm it exists and re-resolve when it does not.
        try:
            client.describe_nodegroup(
                clusterName=cluster.name,
                nodegroupName=cluster.nodegroup_name,
            )
            return cluster.nodegroup_name
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                logger.exception(e)
                return None
            logger.warning(
                "Recorded nodegroup %s no longer exists on cluster %s for "
                "challenge %s. Re-resolving from AWS.",
                cluster.nodegroup_name,
                cluster.name,
                challenge_pk,
            )
        except BotoCoreError as e:
            logger.exception(e)
            return None

    try:
        nodegroups = client.list_nodegroups(clusterName=cluster.name).get(
            "nodegroups", []
        )
    except (ClientError, BotoCoreError) as e:
        logger.exception(e)
        return None

    if not nodegroups:
        # Also the state during initial cluster setup, before
        # create_eks_nodegroup has run. Nothing to replace yet.
        logger.info(
            "Cluster %s for challenge %s has no nodegroup yet. Skipping.",
            cluster.name,
            challenge_pk,
        )
        return None

    if len(nodegroups) > 1:
        logger.error(
            "Cluster %s for challenge %s has %s nodegroups and none recorded. "
            "Refusing to guess which one to replace.",
            cluster.name,
            challenge_pk,
            len(nodegroups),
        )
        return None

    nodegroup_name = nodegroups[0]
    try:
        ChallengeEvaluationCluster.objects.filter(
            challenge_id=challenge_pk
        ).update(nodegroup_name=nodegroup_name)
    except DatabaseError as e:
        logger.exception(e)

    return nodegroup_name


@app.task(bind=True, max_retries=settings.EKS_NODEGROUP_SYNC_MAX_RETRIES)
def recreate_eks_nodegroup(self, challenge_pk):
    """
    Replace a challenge's EKS nodegroup so immutable config changes take effect.

    instanceTypes, amiType and diskSize cannot be changed on an existing
    managed nodegroup, so editing those fields on the challenge has no effect
    on AWS until the nodegroup is recreated. The configuration is validated
    before the old nodegroup is deleted, because deletion is not reversible.

    Deleting the nodegroup terminates any nodes currently running submissions.

    Arguments:
        challenge_pk {int} -- challenge primary key
    Returns:
        {dict} -- {"message": ...} on success, {"error": ...} otherwise
    """
    from .utils import get_aws_credentials_for_challenge

    challenge, cluster = _get_challenge_cluster(challenge_pk)
    if challenge is None:
        return {"error": "No nodegroup to recreate."}

    cluster_name = cluster.name
    client = get_boto3_client(
        "eks", get_aws_credentials_for_challenge(challenge_pk)
    )
    nodegroup_name = _resolve_nodegroup_name(client, challenge_pk, cluster)
    if nodegroup_name is None:
        return {"error": "No nodegroup to recreate."}

    # A nodegroup that is not ACTIVE is being created, updated or deleted by
    # someone else, most likely the initial setup_eks_cluster chain still in
    # flight. Deleting it here would make create_eks_nodegroup fail on a
    # duplicate name and skip starting the code-upload worker.
    try:
        status = client.describe_nodegroup(
            clusterName=cluster_name, nodegroupName=nodegroup_name
        )["nodegroup"]["status"]
    except (ClientError, BotoCoreError, KeyError) as e:
        logger.exception(e)
        return {"error": str(e)}

    if status != "ACTIVE":
        # Most often the initial setup_eks_cluster chain is still building this
        # nodegroup. Giving up here would drop the edit for good: the callback
        # has already refreshed its snapshots, so saving the same value again
        # dispatches nothing. Retry until the nodegroup settles instead.
        message = (
            "Nodegroup {} for challenge {} is {}, not ACTIVE. Retrying "
            "recreate.".format(nodegroup_name, challenge_pk, status)
        )
        logger.warning(message)
        try:
            self.retry(countdown=settings.EKS_NODEGROUP_SYNC_RETRY_SECONDS)
        except MaxRetriesExceededError:
            logger.error(
                "Nodegroup %s for challenge %s never became ACTIVE. Its "
                "worker configuration change was not applied; use the "
                "'Recreate EKS nodegroup' admin action to retry.",
                nodegroup_name,
                challenge_pk,
            )
        return {"error": message}

    errors = validate_eks_nodegroup_config(challenge, client, cluster_name)
    if errors:
        message = (
            "Refusing to recreate nodegroup {} for challenge {}. The existing "
            "nodegroup was left untouched. Problems: {}".format(
                nodegroup_name, challenge_pk, "; ".join(errors)
            )
        )
        logger.error(message)
        return {"error": message}

    logger.warning(
        "Recreating nodegroup %s for challenge %s. Any submissions running on "
        "its nodes will be terminated.",
        nodegroup_name,
        challenge_pk,
    )

    try:
        client.delete_nodegroup(
            clusterName=cluster_name, nodegroupName=nodegroup_name
        )
        client.get_waiter("nodegroup_deleted").wait(
            clusterName=cluster_name, nodegroupName=nodegroup_name
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            logger.exception(e)
            return {"error": str(e)}
        # Nothing to delete; fall through and create the nodegroup.
        logger.info("Nodegroup %s did not exist. Creating it.", nodegroup_name)
    except BotoCoreError as e:
        # Covers WaiterError when deletion outlasts the poll budget. Creating
        # over a half-deleted nodegroup would fail, so stop here.
        logger.exception(e)
        return {"error": str(e)}

    response = create_nodegroup_for_challenge(
        client, challenge, cluster_name, nodegroup_name
    )
    if response is None:
        message = (
            "Deleted nodegroup {} for challenge {} but could not recreate it. "
            "The challenge has no worker capacity until this is "
            "resolved.".format(nodegroup_name, challenge_pk)
        )
        logger.error(message)
        return {"error": message}

    message = "Recreated nodegroup {} for challenge {}.".format(
        nodegroup_name, challenge_pk
    )
    logger.info(message)
    return {"message": message}


@app.task(bind=True, max_retries=settings.EKS_NODEGROUP_SYNC_MAX_RETRIES)
def update_eks_nodegroup_scaling(self, challenge_pk):
    """
    Push a challenge's scaling bounds to its existing EKS nodegroup.

    Unlike instance type, scaling config is mutable, so this needs no
    recreation. Only the bounds are pushed: the live desiredSize is preserved,
    because the autoscale Lambda owns it and will have raised it for pending
    submissions. Sending the challenge's stored desired_worker_instance instead
    would shrink a busy nodegroup and kill running submissions.

    maxSize is the durable field here, since the Lambda caps scale-up at the
    challenge's max_worker_instance.

    Arguments:
        challenge_pk {int} -- challenge primary key
    Returns:
        {dict} -- {"message": ...} on success, {"error": ...} otherwise
    """
    from .utils import get_aws_credentials_for_challenge

    challenge, cluster = _get_challenge_cluster(challenge_pk)
    if challenge is None:
        return {"error": "No nodegroup to update."}

    cluster_name = cluster.name
    client = get_boto3_client(
        "eks", get_aws_credentials_for_challenge(challenge_pk)
    )
    nodegroup_name = _resolve_nodegroup_name(client, challenge_pk, cluster)
    if nodegroup_name is None:
        return {"error": "No nodegroup to update."}

    min_size = challenge.min_worker_instance
    max_size = challenge.max_worker_instance
    try:
        nodegroup = client.describe_nodegroup(
            clusterName=cluster_name, nodegroupName=nodegroup_name
        )["nodegroup"]
        status = nodegroup["status"]
        # Keep whatever the Lambda last decided, but inside the new bounds so
        # AWS does not reject the update.
        desired_size = min(
            max(int(nodegroup["scalingConfig"]["desiredSize"]), min_size),
            max_size,
        )
    except (ClientError, BotoCoreError, KeyError, TypeError, ValueError) as e:
        logger.exception(e)
        return {"error": str(e)}

    if status != "ACTIVE":
        # Same window as recreate_eks_nodegroup: the snapshots are already
        # refreshed, so dropping this would lose the edit permanently.
        message = (
            "Nodegroup {} for challenge {} is {}, not ACTIVE. Retrying "
            "scaling update.".format(nodegroup_name, challenge_pk, status)
        )
        logger.warning(message)
        try:
            self.retry(countdown=settings.EKS_NODEGROUP_SYNC_RETRY_SECONDS)
        except MaxRetriesExceededError:
            logger.error(
                "Nodegroup %s for challenge %s never became ACTIVE. Its "
                "scaling change was not applied; use the 'Recreate EKS "
                "nodegroup' admin action to retry.",
                nodegroup_name,
                challenge_pk,
            )
        return {"error": message}

    try:
        client.update_nodegroup_config(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name,
            scalingConfig={
                "minSize": min_size,
                "maxSize": max_size,
                "desiredSize": desired_size,
            },
        )
    except (ClientError, BotoCoreError) as e:
        logger.exception(e)
        return {"error": str(e)}

    message = (
        "Updated scaling config for nodegroup {} of challenge {}.".format(
            nodegroup_name, challenge_pk
        )
    )
    logger.info(message)
    return {"message": message}


def eks_nodegroup_config_change_callback(instance):
    """
    Dispatch nodegroup work when a challenge's worker configuration changes.

    Called from the Challenge post_save hook. Immutable fields require a full
    recreate; scaling fields only need an update. When both changed, the
    recreate already applies the new scaling config, so only it is dispatched.

    Arguments:
        instance {<class 'apps.challenges.models.Challenge'>} -- challenge instance
    Returns:
        {str or None} -- the action dispatched, for logging and tests
    """
    from base.utils import is_model_field_changed

    if settings.DEBUG or settings.TEST:
        return None

    if not instance.is_docker_based or instance.remote_evaluation:
        return None

    immutable_changed = [
        field
        for field in settings.EKS_NODEGROUP_IMMUTABLE_FIELDS
        if is_model_field_changed(instance, field)
    ]
    scaling_changed = [
        field
        for field in settings.EKS_NODEGROUP_SCALING_FIELDS
        if is_model_field_changed(instance, field)
    ]

    if not immutable_changed and not scaling_changed:
        return None

    for field in (
        settings.EKS_NODEGROUP_IMMUTABLE_FIELDS
        + settings.EKS_NODEGROUP_SCALING_FIELDS
    ):
        setattr(
            instance, "_original_{}".format(field), getattr(instance, field)
        )

    if immutable_changed:
        logger.info(
            "Challenge %s changed %s. Recreating its EKS nodegroup.",
            instance.pk,
            ", ".join(immutable_changed),
        )
        recreate_eks_nodegroup.delay(instance.pk)
        return "recreate"

    logger.info(
        "Challenge %s changed %s. Updating its EKS nodegroup scaling.",
        instance.pk,
        ", ".join(scaling_changed),
    )
    update_eks_nodegroup_scaling.delay(instance.pk)
    return "scale"


def setup_eks_autoscale_cross_account_role(iam_client, challenge_obj):
    """
    Provision the role the autoscale Lambda assumes in a challenge's own AWS
    account.

    Challenges using host credentials run their EKS cluster in the host's
    account, so the Lambda's own execution role cannot reach the nodegroup.
    Without this role every such challenge silently fails to scale with an
    AccessDeniedException on eks:ListNodegroups.

    This is best-effort: failures are logged but never abort cluster setup,
    since the cluster itself is still usable without autoscaling.

    Arguments:
        iam_client -- boto3 IAM client authenticated with the host's credentials
        challenge_obj {<class 'apps.challenges.models.Challenge'>} -- challenge instance
    Returns:
        {str or None} -- ARN of the cross-account role, or None when skipped
    """
    if not challenge_obj.use_host_credentials:
        # Same-account challenges are reachable with the Lambda's own role.
        return None

    lambda_role_arn = settings.EKS_AUTOSCALE_LAMBDA_ROLE_ARN
    if not lambda_role_arn:
        logger.warning(
            "EKS_AUTOSCALE_LAMBDA_ROLE_ARN is not configured. Skipping "
            "cross-account autoscale role creation for challenge %s. EKS "
            "node autoscaling will not work for this challenge until the "
            "role is created manually.",
            challenge_obj.pk,
        )
        return None

    role_name = settings.EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME
    trust_relation = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": lambda_role_arn},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        response = iam_client.create_role(
            RoleName=role_name,
            Description="EvalAI cross-account EKS nodegroup autoscaling role",
            AssumeRolePolicyDocument=json.dumps(trust_relation),
        )
        role_arn = response["Role"]["Arn"]
        waiter = iam_client.get_waiter("role_exists")
        waiter.wait(RoleName=role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            logger.exception(e)
            return None
        # The role is shared across all challenges in a host account, so it
        # already existing is the common case. Refresh its trust policy so a
        # rotated Lambda role ARN does not leave the role unusable.
        try:
            iam_client.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=json.dumps(trust_relation),
            )
            role_arn = iam_client.get_role(RoleName=role_name)["Role"]["Arn"]
        except (ClientError, BotoCoreError) as err:
            logger.exception(err)
            return None
    except BotoCoreError as e:
        # Covers WaiterError, which the role_exists waiter raises when IAM's
        # eventual consistency outlasts the poll budget. It is not a
        # ClientError, so without this the exception would escape a function
        # documented as best-effort.
        logger.exception(e)
        return None

    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=settings.EKS_AUTOSCALE_CROSS_ACCOUNT_POLICY_NAME,
            PolicyDocument=json.dumps(
                settings.EKS_AUTOSCALE_CROSS_ACCOUNT_POLICY_DOCUMENT
            ),
        )
    except (ClientError, BotoCoreError) as e:
        logger.exception(e)
        return None

    logger.info(
        "Cross-account autoscale role ready for challenge %s: %s",
        challenge_obj.pk,
        role_arn,
    )
    return role_arn


@app.task
def setup_eks_cluster(challenge):
    """
    Creates EKS and NodeGroup ARN roles

    Arguments:
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
    """
    from .models import ChallengeEvaluationCluster
    from .serializers import ChallengeEvaluationClusterSerializer
    from .utils import get_aws_credentials_for_challenge

    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    challenge_aws_keys = get_aws_credentials_for_challenge(challenge_obj.pk)
    client = get_boto3_client("iam", challenge_aws_keys)
    environment_suffix = "{}-{}".format(challenge_obj.pk, settings.ENVIRONMENT)
    eks_role_name = "evalai-code-upload-eks-role-{}".format(environment_suffix)
    eks_arn_role = None
    try:
        response = client.create_role(
            RoleName=eks_role_name,
            Description="Amazon EKS cluster role with managed policy",
            AssumeRolePolicyDocument=json.dumps(
                settings.EKS_CLUSTER_TRUST_RELATION
            ),
        )
        eks_arn_role = response["Role"]["Arn"]
    except ClientError as e:
        logger.exception(e)
        return
    waiter = client.get_waiter("role_exists")
    waiter.wait(RoleName=eks_role_name)

    try:
        # Attach AWS managed EKS cluster policy to the role
        response = client.attach_role_policy(
            RoleName=eks_role_name,
            PolicyArn=settings.EKS_CLUSTER_POLICY,
        )
    except ClientError as e:
        logger.exception(e)
        return

    node_group_role_name = "evalai-code-upload-nodegroup-role-{}".format(
        environment_suffix
    )
    node_group_arn_role = None
    try:
        response = client.create_role(
            RoleName=node_group_role_name,
            Description="Amazon EKS node group role with managed policy",
            AssumeRolePolicyDocument=json.dumps(
                settings.EKS_NODE_GROUP_TRUST_RELATION
            ),
        )
        node_group_arn_role = response["Role"]["Arn"]
    except ClientError as e:
        logger.exception(e)
        return
    waiter = client.get_waiter("role_exists")
    waiter.wait(RoleName=node_group_role_name)

    task_execution_policies = settings.EKS_NODE_GROUP_POLICIES
    for policy_arn in task_execution_policies:
        try:
            # Attach AWS managed EKS worker node policy to the role
            response = client.attach_role_policy(
                RoleName=node_group_role_name,
                PolicyArn=policy_arn,
            )
        except ClientError as e:
            logger.exception(e)
            return

    # Create custom ECR all access policy and attach to node_group_role
    ecr_all_access_policy_name = "AWS-ECR-Full-Access-{}".format(
        environment_suffix
    )
    ecr_all_access_policy_arn = None
    try:
        response = client.create_policy(
            PolicyName=ecr_all_access_policy_name,
            PolicyDocument=json.dumps(settings.ECR_ALL_ACCESS_POLICY_DOCUMENT),
        )
        ecr_all_access_policy_arn = response["Policy"]["Arn"]
        waiter = client.get_waiter("policy_exists")
        waiter.wait(PolicyArn=ecr_all_access_policy_arn)
        # Attach custom ECR policy
        response = client.attach_role_policy(
            RoleName=node_group_role_name, PolicyArn=ecr_all_access_policy_arn
        )
    except ClientError as e:
        logger.exception(e)
        return

    # Provision the role the autoscale Lambda assumes for host-credential
    # challenges. Best-effort: never blocks cluster setup. The broad catch is
    # deliberate — the cluster and its persisted config matter far more than
    # an optional autoscaling role, so no failure mode here may reach the
    # ChallengeEvaluationCluster save and subnet creation below.
    try:
        setup_eks_autoscale_cross_account_role(client, challenge_obj)
    except Exception as e:
        logger.exception(e)

    try:
        challenge_evaluation_cluster = ChallengeEvaluationCluster.objects.get(
            challenge=challenge_obj
        )
        serializer = ChallengeEvaluationClusterSerializer(
            challenge_evaluation_cluster,
            data={
                "eks_arn_role": eks_arn_role,
                "node_group_arn_role": node_group_arn_role,
                "ecr_all_access_policy_arn": ecr_all_access_policy_arn,
            },
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
        # Create eks cluster vpc and subnets
        create_eks_cluster_subnets.delay(challenge)
    except Exception as e:
        logger.exception(e)
        return


@app.task
def create_eks_cluster_subnets(challenge):
    """
    Creates EKS and NodeGroup ARN roles

    Arguments:
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
    """
    from .models import ChallengeEvaluationCluster
    from .serializers import ChallengeEvaluationClusterSerializer
    from .utils import get_aws_credentials_for_challenge

    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    challenge_aws_keys = get_aws_credentials_for_challenge(challenge_obj.pk)
    environment_suffix = "{}-{}".format(challenge_obj.pk, settings.ENVIRONMENT)
    client = get_boto3_client("ec2", challenge_aws_keys)
    vpc_ids = []
    try:
        response = client.create_vpc(CidrBlock=challenge_obj.vpc_cidr)
        vpc_ids.append(response["Vpc"]["VpcId"])
    except ClientError as e:
        logger.exception(e)
        return

    waiter = client.get_waiter("vpc_available")
    waiter.wait(VpcIds=vpc_ids)

    # Create internet gateway and attach to vpc
    try:
        # Enable DNS resolution for VPC
        response = client.modify_vpc_attribute(
            EnableDnsHostnames={"Value": True}, VpcId=vpc_ids[0]
        )

        response = client.create_internet_gateway()
        internet_gateway_id = response["InternetGateway"]["InternetGatewayId"]
        client.attach_internet_gateway(
            InternetGatewayId=internet_gateway_id, VpcId=vpc_ids[0]
        )

        # Create and attach route table
        response = client.create_route_table(VpcId=vpc_ids[0])
        route_table_id = response["RouteTable"]["RouteTableId"]
        client.create_route(
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=internet_gateway_id,
            RouteTableId=route_table_id,
        )

        # Create subnets
        subnet_ids = []
        response = client.create_subnet(
            CidrBlock=challenge_obj.subnet_1_cidr,
            AvailabilityZone="us-east-1a",
            VpcId=vpc_ids[0],
        )
        subnet_1_id = response["Subnet"]["SubnetId"]
        subnet_ids.append(subnet_1_id)

        response = client.create_subnet(
            CidrBlock=challenge_obj.subnet_2_cidr,
            AvailabilityZone="us-east-1b",
            VpcId=vpc_ids[0],
        )
        subnet_2_id = response["Subnet"]["SubnetId"]
        subnet_ids.append(subnet_2_id)

        waiter = client.get_waiter("subnet_available")
        waiter.wait(SubnetIds=subnet_ids)

        # Creating managed node group needs subnets to auto assign ip v4
        for subnet_id in subnet_ids:
            response = client.modify_subnet_attribute(
                MapPublicIpOnLaunch={
                    "Value": True,
                },
                SubnetId=subnet_id,
            )

        # Associate route table with subnets
        response = client.associate_route_table(
            RouteTableId=route_table_id,
            SubnetId=subnet_1_id,
        )

        response = client.associate_route_table(
            RouteTableId=route_table_id,
            SubnetId=subnet_2_id,
        )

        # Create security group
        response = client.create_security_group(
            GroupName="EvalAI code upload challenge",
            Description="EvalAI code upload challenge worker group",
            VpcId=vpc_ids[0],
        )
        security_group_id = response["GroupId"]

        response = client.create_security_group(
            GroupName="evalai-code-upload-challenge-efs-{}".format(
                environment_suffix
            ),
            Description="EKS nodegroup EFS",
            VpcId=vpc_ids[0],
        )
        efs_security_group_id = response["GroupId"]

        response = client.authorize_security_group_ingress(
            GroupId=efs_security_group_id,
            IpPermissions=[
                {
                    "FromPort": 2049,
                    "IpProtocol": "tcp",
                    "IpRanges": [
                        {
                            "CidrIp": challenge_obj.vpc_cidr,
                        },
                    ],
                    "ToPort": 2049,
                }
            ],
        )

        # Create EFS
        efs_client = get_boto3_client("efs", challenge_aws_keys)
        efs_creation_token = str(uuid.uuid4())[:64]
        response = efs_client.create_file_system(
            CreationToken=efs_creation_token,
        )
        efs_id = response["FileSystemId"]

        challenge_evaluation_cluster = ChallengeEvaluationCluster.objects.get(
            challenge=challenge_obj
        )
        serializer = ChallengeEvaluationClusterSerializer(
            challenge_evaluation_cluster,
            data={
                "vpc_id": vpc_ids[0],
                "internet_gateway_id": internet_gateway_id,
                "route_table_id": route_table_id,
                "security_group_id": security_group_id,
                "subnet_1_id": subnet_1_id,
                "subnet_2_id": subnet_2_id,
                "efs_security_group_id": efs_security_group_id,
                "efs_id": efs_id,
                "efs_creation_token": efs_creation_token,
            },
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
        # Create eks cluster
        create_eks_cluster.delay(challenge)
    except ClientError as e:
        logger.exception(e)
        return


@app.task
def create_eks_cluster(challenge):
    """
    Called when Challenge is approved by the EvalAI admin
    calls the create_eks_nodegroup function

    Arguments:
        sender {type} -- model field called the post hook
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
    """
    from .models import ChallengeEvaluationCluster
    from .serializers import ChallengeEvaluationClusterSerializer
    from .utils import get_aws_credentials_for_challenge

    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    environment_suffix = "{}-{}".format(challenge_obj.pk, settings.ENVIRONMENT)
    cluster_name = "{}-{}-cluster".format(
        challenge_obj.title.replace(" ", "-"), environment_suffix
    )
    if challenge_obj.approved_by_admin and challenge_obj.is_docker_based:
        challenge_aws_keys = get_aws_credentials_for_challenge(
            challenge_obj.pk
        )
        client = get_boto3_client("eks", challenge_aws_keys)
        cluster_meta = get_code_upload_setup_meta_for_challenge(
            challenge_obj.pk
        )
        try:
            response = client.create_cluster(
                name=cluster_name,
                version="1.29",
                roleArn=cluster_meta["EKS_CLUSTER_ROLE_ARN"],
                resourcesVpcConfig={
                    "subnetIds": [
                        cluster_meta["SUBNET_1"],
                        cluster_meta["SUBNET_2"],
                    ],
                    "securityGroupIds": [
                        cluster_meta["SUBNET_SECURITY_GROUP"]
                    ],
                },
            )
            waiter = client.get_waiter("cluster_active")
            waiter.wait(name=cluster_name)
            # creating kubeconfig
            cluster = client.describe_cluster(name=cluster_name)
            cluster_cert = cluster["cluster"]["certificateAuthority"]["data"]
            cluster_ep = cluster["cluster"]["endpoint"]
            cluster_config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {
                        "cluster": {
                            "server": str(cluster_ep),
                            "certificate-authority-data": str(cluster_cert),
                        },
                        "name": "kubernetes",
                    }
                ],
                "contexts": [
                    {
                        "context": {"cluster": "kubernetes", "user": "aws"},
                        "name": "aws",
                    }
                ],
                "current-context": "aws",
                "preferences": {},
                "users": [
                    {
                        "name": "aws",
                        "user": {
                            "exec": {
                                "apiVersion": "client.authentication.k8s.io/v1alpha1",
                                "command": "heptio-authenticator-aws",
                                "args": ["token", "-i", cluster_name],
                            }
                        },
                    }
                ],
            }

            # Write in YAML.
            config_text = yaml.dump(cluster_config, default_flow_style=False)
            config_file = NamedTemporaryFile(delete=True)
            config_file.write(config_text.encode())
            challenge_evaluation_cluster = (
                ChallengeEvaluationCluster.objects.get(challenge=challenge_obj)
            )

            efs_client = get_boto3_client("efs", challenge_aws_keys)
            # Create mount targets for subnets
            mount_target_ids = []
            response = efs_client.create_mount_target(
                FileSystemId=challenge_evaluation_cluster.efs_id,
                SubnetId=challenge_evaluation_cluster.subnet_1_id,
                SecurityGroups=[
                    challenge_evaluation_cluster.efs_security_group_id
                ],
            )
            mount_target_ids.append(response["MountTargetId"])

            response = efs_client.create_mount_target(
                FileSystemId=challenge_evaluation_cluster.efs_id,
                SubnetId=challenge_evaluation_cluster.subnet_2_id,
                SecurityGroups=[
                    challenge_evaluation_cluster.efs_security_group_id
                ],
            )
            mount_target_ids.append(response["MountTargetId"])

            serializer = ChallengeEvaluationClusterSerializer(
                challenge_evaluation_cluster,
                data={
                    "name": cluster_name,
                    "cluster_endpoint": cluster_ep,
                    "cluster_ssl": cluster_cert,
                    "efs_mount_target_ids": mount_target_ids,
                },
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
            # Creating nodegroup
            create_eks_nodegroup.delay(challenge, cluster_name)
            return response
        except ClientError as e:
            logger.exception(e)
            return


def challenge_approval_callback(sender, instance, field_name, **kwargs):
    """This is to check if a challenge has been approved or disapproved since last time.

    On approval of a challenge, it launches a worker on Fargate.
    On disapproval, it scales down the workers to 0, and deletes the challenge's service on Fargate.

    Arguments:
        sender -- The model which initated this callback (Challenge)
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model (a challenge object)
        field_name {str} -- The name of the field to check for a change (approved_by_admin)

    """
    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))
    challenge = instance
    challenge._original_approved_by_admin = curr

    if (
        not challenge.is_docker_based
        and not challenge.uses_ec2_worker
        and challenge.remote_evaluation is False
    ):
        if curr and not prev:
            if not challenge.workers:
                response = start_workers([challenge])
                count, failures = response["count"], response["failures"]
                if not count:
                    logger.error(
                        "Worker for challenge {} couldn't start! Error: {}".format(
                            challenge.id, failures[0]["message"]
                        )
                    )
                else:
                    construct_and_send_worker_start_mail(challenge)

        if prev and not curr:
            if challenge.workers:
                response = delete_workers([challenge])
                count, failures = response["count"], response["failures"]
                if not count:
                    logger.error(
                        "Worker for challenge {} couldn't be deleted! Error: {}".format(
                            challenge.id, failures[0]["message"]
                        )
                    )


@app.task
def setup_ec2(challenge):
    """
    Creates EC2 instance for the challenge and spawns a worker container.

    Arguments:
        challenge {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
    """
    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    if challenge_obj.ec2_instance_id:
        return start_ec2_instance(challenge_obj)
    return create_ec2_instance(challenge_obj)


@app.task
def update_sqs_retention_period_task(challenge):
    """
    Updates sqs retention period for a challenge when the attribute is changed.

    Arguments:
        challenge {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
    """
    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    return update_sqs_retention_period(challenge_obj)
