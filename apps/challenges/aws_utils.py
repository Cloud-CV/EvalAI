import json
import logging
import os
import random
import string
import uuid
import yaml

from botocore.exceptions import ClientError
from django.conf import settings
from django.core import serializers
from django.core.files.temp import NamedTemporaryFile
from http import HTTPStatus

from .challenge_notification_util import (
    construct_and_send_worker_start_mail,
    construct_and_send_eks_cluster_creation_mail,
)

from base.utils import get_boto3_client, send_email
from evalai.celery import app
from accounts.models import JwtToken

logger = logging.getLogger(__name__)

DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
ENV = DJANGO_SETTINGS_MODULE.split(".")[-1]
EVALAI_DNS = os.environ.get("SERVICE_DNS")
aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get(
        "AWS_STORAGE_BUCKET_NAME", "evalai-s3-bucket"
    ),
}


COMMON_SETTINGS_DICT = {
    "EXECUTION_ROLE_ARN": os.environ.get(
        "EXECUTION_ROLE_ARN",
        "arn:aws:iam::{}:role/evalaiTaskExecutionRole".format(
            aws_keys["AWS_ACCOUNT_ID"]
        ),
    ),
    "WORKER_IMAGE": os.environ.get(
        "WORKER_IMAGE",
        "{}.dkr.ecr.us-east-1.amazonaws.com/evalai-{}-worker:latest".format(
            aws_keys["AWS_ACCOUNT_ID"], ENV
        ),
    ),
    "CODE_UPLOAD_WORKER_IMAGE": os.environ.get(
        "CODE_UPLOAD_WORKER_IMAGE",
        "{}.dkr.ecr.us-east-1.amazonaws.com/evalai-{}-worker:latest".format(
            aws_keys["AWS_ACCOUNT_ID"], ENV
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


task_definition = """
{{
    "family":"{queue_name}",
    "executionRoleArn":"{EXECUTION_ROLE_ARN}",
    "networkMode":"awsvpc",
    "containerDefinitions":[
        {{
            "name": "{container_name}",
            "image": "{WORKER_IMAGE}",
            "essential": True,
            "environment": [
                {{
                  "name": "AWS_DEFAULT_REGION",
                  "value": "{AWS_REGION}"
                }},
                {{
                  "name": "AWS_ACCOUNT_ID",
                  "value": "{AWS_ACCOUNT_ID}"
                }},
                {{
                  "name": "AWS_ACCESS_KEY_ID",
                  "value": "{AWS_ACCESS_KEY_ID}"
                }},
                {{
                  "name": "AWS_SECRET_ACCESS_KEY",
                  "value": "{AWS_SECRET_ACCESS_KEY}"
                }},
                {{
                  "name": "AWS_STORAGE_BUCKET_NAME",
                  "value": "{AWS_STORAGE_BUCKET_NAME}"
                }},
                {{
                  "name": "CHALLENGE_PK",
                  "value": "{challenge_pk}"
                }},
                {{
                  "name": "CHALLENGE_QUEUE",
                  "value": "{queue_name}"
                }},
                {{
                  "name": "DJANGO_SERVER",
                  "value": "{DJANGO_SERVER}"
                }},
                {{
                  "name": "DJANGO_SETTINGS_MODULE",
                  "value": "settings.{ENV}"
                }},
                {{
                  "name": "DEBUG",
                  "value": "{DEBUG}"
                }},
                {{
                  "name": "EMAIL_HOST",
                  "value": "{EMAIL_HOST}"
                }},
                {{
                  "name": "EMAIL_HOST_PASSWORD",
                  "value": "{EMAIL_HOST_PASSWORD}"
                }},
                {{
                  "name": "EMAIL_HOST_USER",
                  "value": "{EMAIL_HOST_USER}"
                }},
                {{
                  "name": "EMAIL_PORT",
                  "value": "{EMAIL_PORT}"
                }},
                {{
                  "name": "EMAIL_USE_TLS",
                  "value": "{EMAIL_USE_TLS}"
                }},
                {{
                  "name": "MEMCACHED_LOCATION",
                  "value": "{MEMCACHED_LOCATION}"
                }},
                {{
                    "name": "PYTHONUNBUFFERED",
                    "value": "1"
                }},
                {{
                  "name": "RDS_DB_NAME",
                  "value": "{RDS_DB_NAME}"
                }},
                {{
                  "name": "RDS_HOSTNAME",
                  "value": "{RDS_HOSTNAME}"
                }},
                {{
                  "name": "RDS_PASSWORD",
                  "value": "{RDS_PASSWORD}"
                }},
                {{
                  "name": "RDS_USERNAME",
                  "value": "{RDS_USERNAME}"
                }},
                {{
                  "name": "RDS_PORT",
                  "value": "{RDS_PORT}"
                }},
                {{
                  "name": "SECRET_KEY",
                  "value": "{SECRET_KEY}"
                }},
                {{
                  "name": "SENTRY_URL",
                  "value": "{SENTRY_URL}"
                }},
                {{
                    "name": "AWS_SES_REGION_NAME",
                    "value": "{AWS_SES_REGION_NAME}"
                }},
                {{
                    "name": "AWS_SES_REGION_ENDPOINT",
                    "value": "{AWS_SES_REGION_ENDPOINT}"
                }}
            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "{log_group_name}",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "{queue_name}",
                    "awslogs-create-group": "true",
                }},
            }},
        }}
    ],
    "requiresCompatibilities":[
        "FARGATE"
    ],
    "cpu": "{CPU}",
    "memory": "{MEMORY}",
}}
"""

task_definition_code_upload_worker = """
{{
    "family":"{queue_name}",
    "executionRoleArn":"{EXECUTION_ROLE_ARN}",
    "networkMode":"awsvpc",
    "containerDefinitions":[
        {{
            "name": "{code_upload_container_name}",
            "image": "{CODE_UPLOAD_WORKER_IMAGE}",
            "essential": True,
            "environment": [
                {{
                  "name": "AWS_DEFAULT_REGION",
                  "value": "{AWS_REGION}"
                }},
                {{
                  "name": "AWS_ACCESS_KEY_ID",
                  "value": "{AWS_ACCESS_KEY_ID}"
                }},
                {{
                  "name": "AWS_SECRET_ACCESS_KEY",
                  "value": "{AWS_SECRET_ACCESS_KEY}"
                }},
                {{
                  "name": "CLUSTER_NAME",
                  "value": "{cluster_name}"
                }},
                {{
                  "name": "CLUSTER_ENDPOINT",
                  "value": "{cluster_endpoint}"
                }},
                {{
                  "name": "CERTIFICATE",
                  "value": "{certificate}"
                }},
                {{
                  "name": "CIDR",
                  "value": "{CIDR}"
                }},
                {{
                  "name": "QUEUE_NAME",
                  "value": "{queue_name}"
                }},
                {{
                  "name": "EVALAI_API_SERVER",
                  "value": "{EVALAI_API_SERVER}"
                }},

                {{
                    "name": "AUTH_TOKEN",
                    "value": "{auth_token}"
                }},

                {{
                    "name": "EVALAI_DNS",
                    "value": "{EVALAI_DNS}"
                }},

                {{
                    "name": "EFS_ID",
                    "value": "{EFS_ID}"
                }}

            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "{log_group_name}",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "{queue_name}",
                    "awslogs-create-group": "true",
                }},
            }},
        }}
    ],
    "requiresCompatibilities":[
        "FARGATE"
    ],
    "cpu": "{CPU}",
    "memory": "{MEMORY}",
}}
"""

task_definition_static_code_upload_worker = """
{{
    "family":"{queue_name}",
    "executionRoleArn":"{EXECUTION_ROLE_ARN}",
    "networkMode":"awsvpc",
    "containerDefinitions":[
        {{
            "name": "{code_upload_container_name}",
            "image": "{CODE_UPLOAD_WORKER_IMAGE}",
            "essential": True,
            "environment": [
                {{
                  "name": "AWS_DEFAULT_REGION",
                  "value": "{AWS_REGION}"
                }},
                {{
                  "name": "AWS_ACCESS_KEY_ID",
                  "value": "{AWS_ACCESS_KEY_ID}"
                }},
                {{
                  "name": "AWS_SECRET_ACCESS_KEY",
                  "value": "{AWS_SECRET_ACCESS_KEY}"
                }},
                {{
                  "name": "CLUSTER_NAME",
                  "value": "{cluster_name}"
                }},
                {{
                  "name": "CLUSTER_ENDPOINT",
                  "value": "{cluster_endpoint}"
                }},
                {{
                  "name": "CERTIFICATE",
                  "value": "{certificate}"
                }},
                {{
                  "name": "CIDR",
                  "value": "{CIDR}"
                }},
                {{
                  "name": "QUEUE_NAME",
                  "value": "{queue_name}"
                }},
                {{
                  "name": "EVALAI_API_SERVER",
                  "value": "{EVALAI_API_SERVER}"
                }},

                {{
                    "name": "AUTH_TOKEN",
                    "value": "{auth_token}"
                }},

                {{
                    "name": "EVALAI_DNS",
                    "value": "{EVALAI_DNS}"
                }},

                {{
                    "name": "EFS_ID",
                    "value": "{EFS_ID}"
                }}

            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "{log_group_name}",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "{queue_name}",
                    "awslogs-create-group": "true",
                }},
            }},
        }},
        {{
            "name": "{container_name}",
            "image": "{WORKER_IMAGE}",
            "essential": True,
            "environment": [
                {{
                  "name": "AWS_DEFAULT_REGION",
                  "value": "{AWS_REGION}"
                }},
                {{
                  "name": "AWS_ACCOUNT_ID",
                  "value": "{AWS_ACCOUNT_ID}"
                }},
                {{
                  "name": "AWS_ACCESS_KEY_ID",
                  "value": "{AWS_ACCESS_KEY_ID}"
                }},
                {{
                  "name": "AWS_SECRET_ACCESS_KEY",
                  "value": "{AWS_SECRET_ACCESS_KEY}"
                }},
                {{
                  "name": "AWS_STORAGE_BUCKET_NAME",
                  "value": "{AWS_STORAGE_BUCKET_NAME}"
                }},
                {{
                  "name": "CHALLENGE_PK",
                  "value": "{challenge_pk}"
                }},
                {{
                  "name": "CHALLENGE_QUEUE",
                  "value": "{queue_name}"
                }},
                {{
                  "name": "DJANGO_SERVER",
                  "value": "{DJANGO_SERVER}"
                }},
                {{
                  "name": "DJANGO_SETTINGS_MODULE",
                  "value": "settings.{ENV}"
                }},
                {{
                  "name": "DEBUG",
                  "value": "{DEBUG}"
                }},
                {{
                  "name": "EMAIL_HOST",
                  "value": "{EMAIL_HOST}"
                }},
                {{
                  "name": "EMAIL_HOST_PASSWORD",
                  "value": "{EMAIL_HOST_PASSWORD}"
                }},
                {{
                  "name": "EMAIL_HOST_USER",
                  "value": "{EMAIL_HOST_USER}"
                }},
                {{
                  "name": "EMAIL_PORT",
                  "value": "{EMAIL_PORT}"
                }},
                {{
                  "name": "EMAIL_USE_TLS",
                  "value": "{EMAIL_USE_TLS}"
                }},
                {{
                  "name": "MEMCACHED_LOCATION",
                  "value": "{MEMCACHED_LOCATION}"
                }},
                {{
                    "name": "PYTHONUNBUFFERED",
                    "value": "1"
                }},
                {{
                  "name": "RDS_DB_NAME",
                  "value": "{RDS_DB_NAME}"
                }},
                {{
                  "name": "RDS_HOSTNAME",
                  "value": "{RDS_HOSTNAME}"
                }},
                {{
                  "name": "RDS_PASSWORD",
                  "value": "{RDS_PASSWORD}"
                }},
                {{
                  "name": "RDS_USERNAME",
                  "value": "{RDS_USERNAME}"
                }},
                {{
                  "name": "RDS_PORT",
                  "value": "{RDS_PORT}"
                }},
                {{
                  "name": "SECRET_KEY",
                  "value": "{SECRET_KEY}"
                }},
                {{
                  "name": "SENTRY_URL",
                  "value": "{SENTRY_URL}"
                }},
                {{
                    "name": "AWS_SES_REGION_NAME",
                    "value": "{AWS_SES_REGION_NAME}"
                }},
                {{
                    "name": "AWS_SES_REGION_ENDPOINT",
                    "value": "{AWS_SES_REGION_ENDPOINT}"
                }}
            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "{log_group_name}",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "{queue_name}",
                    "awslogs-create-group": "true",
                }},
            }},
        }}

    ],
    "requiresCompatibilities":[
        "FARGATE"
    ],
    "cpu": "{CPU}",
    "memory": "{MEMORY}",
}}
"""

service_definition = """
{{
    "cluster":"{CLUSTER}",
    "serviceName":"{service_name}",
    "taskDefinition":"{task_def_arn}",
    "desiredCount":1,
    "clientToken":"{client_token}",
    "launchType":"FARGATE",
    "platformVersion":"LATEST",
    "networkConfiguration":{{
        "awsvpcConfiguration": {{
            "subnets": [
                "{SUBNET_1}",
                "{SUBNET_2}",
            ],
            'securityGroups': [
                "{SUBNET_SECURITY_GROUP}",
            ],
            "assignPublicIp": "ENABLED"
        }}
    }},
    "schedulingStrategy":"REPLICA",
    "deploymentController":{{
        "type": "ECS"
    }},
    "deploymentConfiguration":{{
        "deploymentCircuitBreaker":{{
            "enable": True,
            "rollback": False
        }}
    }}
}}
"""

update_service_args = """
{{
    "cluster":"{CLUSTER}",
    "service":"{service_name}",
    "desiredCount":num_of_tasks,
    "taskDefinition":"{task_def_arn}",
    "forceNewDeployment":{force_new_deployment}
}}
"""

delete_service_args = """
{{
    "cluster": "{CLUSTER}",
    "service": "{service_name}",
    "force": False
}}
"""


def get_code_upload_setup_meta_for_challenge(challenge_pk):
    """
    Return the EKS cluster network and arn meta for a challenge
    Arguments:
        challenge_pk {int} -- challenge pk for which credentails are to be fetched
    Returns:
        code_upload_meta {dict} -- Dict containing cluster network and arn meta
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
    log_group_name = "challenge-pk-{}-{}-workers".format(
        challenge_pk, settings.ENVIRONMENT
    )
    return log_group_name


def client_token_generator(challenge_pk):
    """
    Returns a 32 characters long client token to ensure idempotency with create_service boto3 requests.

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
    Registers the task definition of the worker for a challenge, before creating a service.

    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    queue_name (str): queue_name is the queue field of the Challenge model used in many parameters fof the task def.
    challenge (<class 'challenges.models.Challenge'>): The challenge object for whom the task definition is being registered.

    Returns:
    dict: A dict of the task definition and it's ARN if succesful, and an error dictionary if not
    """
    container_name = "worker_{}".format(queue_name)
    code_upload_container_name = "code_upload_worker_{}".format(queue_name)
    worker_cpu_cores = challenge.worker_cpu_cores
    worker_memory = challenge.worker_memory
    log_group_name = get_log_group_name(challenge.pk)
    execution_role_arn = COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"]
    AWS_SES_REGION_NAME = settings.AWS_SES_REGION_NAME
    AWS_SES_REGION_ENDPOINT = settings.AWS_SES_REGION_ENDPOINT

    if execution_role_arn:
        from .utils import get_aws_credentials_for_challenge

        challenge_aws_keys = get_aws_credentials_for_challenge(challenge.pk)
        if challenge.is_docker_based:
            from .models import ChallengeEvaluationCluster

            # Cluster detail to be used by code-upload-worker
            try:
                cluster_details = ChallengeEvaluationCluster.objects.get(
                    challenge=challenge
                )
                cluster_name = cluster_details.name
                cluster_endpoint = cluster_details.cluster_endpoint
                cluster_certificate = cluster_details.cluster_ssl
                efs_id = cluster_details.efs_id
            except ClientError as e:
                logger.exception(e)
                return e.response
            # challenge host auth token to be used by code-upload-worker
            token = JwtToken.objects.get(user=challenge.creator.created_by)
            if challenge.is_static_dataset_docker_based_challenge:
                definition = task_definition_static_code_upload_worker.format(
                    queue_name=queue_name,
                    container_name=container_name,
                    code_upload_container_name=code_upload_container_name,
                    ENV=ENV,
                    challenge_pk=challenge.pk,
                    auth_token=token.refresh_token,
                    cluster_name=cluster_name,
                    cluster_endpoint=cluster_endpoint,
                    certificate=cluster_certificate,
                    CPU=worker_cpu_cores,
                    MEMORY=worker_memory,
                    log_group_name=log_group_name,
                    EVALAI_DNS=EVALAI_DNS,
                    EFS_ID=efs_id,
                    AWS_SES_REGION_NAME=AWS_SES_REGION_NAME,
                    AWS_SES_REGION_ENDPOINT=AWS_SES_REGION_ENDPOINT,
                    **COMMON_SETTINGS_DICT,
                    **challenge_aws_keys,
                )
            else:
                definition = task_definition_code_upload_worker.format(
                    queue_name=queue_name,
                    code_upload_container_name=code_upload_container_name,
                    ENV=ENV,
                    challenge_pk=challenge.pk,
                    auth_token=token.refresh_token,
                    cluster_name=cluster_name,
                    cluster_endpoint=cluster_endpoint,
                    certificate=cluster_certificate,
                    CPU=worker_cpu_cores,
                    MEMORY=worker_memory,
                    log_group_name=log_group_name,
                    EVALAI_DNS=EVALAI_DNS,
                    EFS_ID=efs_id,
                    **COMMON_SETTINGS_DICT,
                    **challenge_aws_keys,
                )
        else:
            definition = task_definition.format(
                queue_name=queue_name,
                container_name=container_name,
                ENV=ENV,
                challenge_pk=challenge.pk,
                CPU=worker_cpu_cores,
                MEMORY=worker_memory,
                log_group_name=log_group_name,
                AWS_SES_REGION_NAME=AWS_SES_REGION_NAME,
                AWS_SES_REGION_ENDPOINT=AWS_SES_REGION_ENDPOINT,
                **COMMON_SETTINGS_DICT,
                **challenge_aws_keys,
            )
        definition = eval(definition)
        if not challenge.task_def_arn:
            try:
                response = client.register_task_definition(**definition)
                if (
                    response["ResponseMetadata"]["HTTPStatusCode"]
                    == HTTPStatus.OK
                ):
                    task_def_arn = response["taskDefinition"][
                        "taskDefinitionArn"
                    ]
                    challenge.task_def_arn = task_def_arn
                    challenge.save()
                return response
            except ClientError as e:
                logger.exception(e)
                return e.response
        else:
            message = "Error. Task definition already registered for challenge {}.".format(
                challenge.pk
            )
            return {
                "Error": message,
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            }
    else:
        message = "Please ensure that the TASK_EXECUTION_ROLE_ARN is appropriately passed as an environment varible."
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }


def create_service_by_challenge_pk(client, challenge, client_token):
    """
    Creates the worker service for a challenge, and sets the number of workers to one.

    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>): The challenge object  for whom the task definition is being registered.
    client_token (str): The client token generated by client_token_generator()

    Returns:
    dict: The response returned by the create_service method from boto3. If unsuccesful, returns an error dictionary
    """

    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
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
        definition = service_definition.format(
            CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
            service_name=service_name,
            task_def_arn=task_def_arn,
            client_token=client_token,
            **VPC_DICT,
        )
        definition = eval(definition)
        try:
            response = client.create_service(**definition)
            if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
                challenge.workers = 1
                challenge.save()
            return response
        except ClientError as e:
            logger.exception(e)
            return e.response
    else:
        message = "Worker service for challenge {} already exists. Please scale, stop or delete.".format(
            challenge.pk
        )
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }


def update_service_by_challenge_pk(
    client, challenge, num_of_tasks, force_new_deployment=False
):
    """
    Updates the worker service for a challenge, and scales the number of workers to num_of_tasks.

    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>): The challenge object  for whom the task definition is being registered.
    num_of_tasks (int): Number of workers to scale to for the challenge.
    force_new_deployment (bool): Set True (mainly for restarting) to specify if you want to redploy with the latest image from ECR. Default is False.

    Returns:
    dict: The response returned by the update_service method from boto3. If unsuccesful, returns an error dictionary
    """

    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    task_def_arn = challenge.task_def_arn

    kwargs = update_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        task_def_arn=task_def_arn,
        force_new_deployment=force_new_deployment,
    )
    kwargs = eval(kwargs)

    try:
        response = client.update_service(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = num_of_tasks
            challenge.save()
        return response
    except ClientError as e:
        logger.exception(e)
        return e.response


def delete_service_by_challenge_pk(challenge):
    """
    Deletes the workers service of a challenge.

    Before deleting, it scales down the number of workers in the service to 0, then proceeds to delete the service.

    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge object for whom the task definition is being registered.

    Returns:
    dict: The response returned by the delete_service method from boto3
    """
    client = get_boto3_client("ecs", aws_keys)
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    kwargs = delete_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        force=True,
    )
    kwargs = eval(kwargs)
    try:
        if challenge.workers != 0:
            response = update_service_by_challenge_pk(
                client, challenge, 0, False
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                return response

        response = client.delete_service(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = None
            challenge.save()
            client.deregister_task_definition(
                taskDefinition=challenge.task_def_arn
            )
            challenge.task_def_arn = ""
            challenge.save()
        return response
    except ClientError as e:
        logger.exception(e)
        return e.response


def service_manager(
    client, challenge, num_of_tasks=None, force_new_deployment=False
):
    """
    This method determines if the challenge is new or not, and accordingly calls <update or create>_by_challenge_pk.

    Called by: Start, Stop & Scale methods for multiple workers.

    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    challenge (): The challenge object for whom the task definition is being registered.
    num_of_tasks: The number of workers to scale to (relevant only if the challenge is not new).
                  default: None

    Returns:
    dict: The response returned by the respective functions update_service_by_challenge_pk or create_service_by_challenge_pk
    """
    if challenge.workers is not None:
        response = update_service_by_challenge_pk(
            client, challenge, num_of_tasks, force_new_deployment
        )
        return response
    else:
        client_token = client_token_generator(challenge.pk)
        response = create_service_by_challenge_pk(
            client, challenge, client_token
        )
        return response


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
            response = "Please scale to a different number. Challenge has {} worker(s).".format(
                num_of_tasks
            )
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
            continue
        response = service_manager(
            client, challenge=challenge, num_of_tasks=num_of_tasks
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
            failures.append(
                {"message": response["Error"], "challenge_pk": challenge.pk}
            )
            continue
        count += 1
    return {"count": count, "failures": failures}


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
        if challenge.is_docker_based:
            response = "Sorry. This feature is not available for code upload/docker based challenges."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
        elif (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(
                client,
                challenge=challenge,
                num_of_tasks=challenge.workers,
                force_new_deployment=True,
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


def restart_workers_signal_callback(sender, instance, field_name, **kwargs):
    """
    Called when either evaluation_script or test_annotation_script for challenge
    is updated, to restart the challenge workers.
    """
    if settings.DEBUG:
        return

    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))

    if field_name == "evaluation_script":
        instance._original_evaluation_script = curr
    elif field_name == "test_annotation":
        instance._original_test_annotation = curr

    if prev != curr:
        challenge = None
        if field_name == "test_annotation":
            challenge = instance.challenge
        else:
            challenge = instance

        response = restart_workers([challenge])

        count, failures = response["count"], response["failures"]

        logger.info(
            "The worker service for challenge {} was restarted, as {} was changed.".format(
                challenge.pk, field_name
            )
        )

        if count != 1:
            logger.warning(
                "Worker(s) for challenge {} couldn't restart! Error: {}".format(
                    challenge.id, failures[0]["message"]
                )
            )
        else:
            challenge_url = "{}/web/challenges/challenge-page/{}".format(
                settings.EVALAI_API_SERVER, challenge.id
            )
            challenge_manage_url = (
                "{}/web/challenges/challenge-page/{}/manage".format(
                    settings.EVALAI_API_SERVER, challenge.id
                )
            )

            if field_name == "test_annotation":
                file_updated = "Test Annotation"
            elif field_name == "evaluation_script":
                file_updated = "Evaluation script"

            template_data = {
                "CHALLENGE_NAME": challenge.title,
                "CHALLENGE_MANAGE_URL": challenge_manage_url,
                "CHALLENGE_URL": challenge_url,
                "FILE_UPDATED": file_updated,
            }

            if challenge.image:
                template_data["CHALLENGE_IMAGE_URL"] = challenge.image.url

            template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get(
                "WORKER_RESTART_EMAIL"
            )

            # Send email notification only when inform_hosts is true
            if challenge.inform_hosts:
                emails = challenge.creator.get_all_challenge_host_email()
                for email in emails:
                    send_email(
                        sender=settings.CLOUDCV_TEAM_EMAIL,
                        recipient=email,
                        template_id=template_id,
                        template_data=template_data,
                    )


def get_logs_from_cloudwatch(
    log_group_name, log_stream_prefix, start_time, end_time, pattern
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
            )
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


@app.task
def create_eks_nodegroup(challenge, cluster_name):
    """
    Creates a nodegroup when a EKS cluster is created by the EvalAI admin
    Arguments:
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
        cluster_name {str} -- name of eks cluster
    """
    from .utils import get_aws_credentials_for_challenge

    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    environment_suffix = "{}-{}".format(challenge_obj.pk, settings.ENVIRONMENT)
    nodegroup_name = "{}-{}-nodegroup".format(
        challenge_obj.title.replace(" ", "-"), environment_suffix
    )
    challenge_aws_keys = get_aws_credentials_for_challenge(challenge_obj.pk)
    client = get_boto3_client("eks", challenge_aws_keys)
    cluster_meta = get_code_upload_setup_meta_for_challenge(challenge_obj.pk)
    # TODO: Move the hardcoded cluster configuration such as the
    # instance_type, subnets, AMI to challenge configuration later.
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
        return
    waiter = client.get_waiter("nodegroup_active")
    waiter.wait(clusterName=cluster_name, nodegroupName=nodegroup_name)
    construct_and_send_eks_cluster_creation_mail(challenge_obj)
    # starting the code-upload-worker
    client = get_boto3_client("ecs", aws_keys)
    client_token = client_token_generator(challenge_obj.pk)
    create_service_by_challenge_pk(client, challenge_obj, client_token)


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
                version="1.15",
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

    if not challenge.is_docker_based and challenge.remote_evaluation is False:
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
