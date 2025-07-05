import json
import logging
import os
import random
import string
import uuid
from http import HTTPStatus

import yaml
from accounts.models import JwtToken
from base.utils import get_boto3_client, send_email
from botocore.exceptions import ClientError
from django.conf import settings
from django.core import serializers
from django.core.files.temp import NamedTemporaryFile

from evalai.celery import app

from .challenge_notification_util import (
    construct_and_send_eks_cluster_creation_mail,
    construct_and_send_worker_start_mail,
)
from .task_definitions import (
    container_definition_code_upload_worker,
    container_definition_submission_worker,
    delete_service_args,
    service_definition,
    task_definition,
    task_definition_code_upload_worker,
    task_definition_static_code_upload_worker,
    update_service_args,
)

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
        "{}.dkr.ecr.us-east-1.amazonaws.com/evalai-{}-worker-py3.7:latest".format(
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
    "STATSD_ENDPOINT": os.environ.get("STATSD_ENDPOINT"),
    "STATSD_PORT": os.environ.get("STATSD_PORT"),
}

VPC_DICT = {
    "SUBNET_1": os.environ.get("SUBNET_1", "subnet1"),
    "SUBNET_2": os.environ.get("SUBNET_2", "subnet2"),
    "SUBNET_SECURITY_GROUP": os.environ.get("SUBNET_SECURITY_GROUP", "sg"),
}


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
    container_name = f"worker_{queue_name}"
    code_upload_container_name = f"code_upload_worker_{queue_name}"
    worker_cpu_cores = challenge.worker_cpu_cores
    worker_memory = challenge.worker_memory
    ephemeral_storage = challenge.ephemeral_storage
    log_group_name = get_log_group_name(challenge.pk)
    execution_role_arn = COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"]
    AWS_SES_REGION_NAME = settings.AWS_SES_REGION_NAME
    AWS_SES_REGION_ENDPOINT = settings.AWS_SES_REGION_ENDPOINT

    if challenge.worker_image_url:
        updated_settings = {
            **COMMON_SETTINGS_DICT,
            "WORKER_IMAGE": challenge.worker_image_url,
        }
    else:
        updated_settings = COMMON_SETTINGS_DICT

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
            if challenge.is_static_dataset_code_upload:
                code_upload_container = (
                    container_definition_code_upload_worker.format(
                        queue_name=queue_name,
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

                    # Update CloudWatch log retention policy when task definition is registered
                    update_challenge_log_retention_on_task_def_registration(
                        challenge
                    )

                return response
            except ClientError as e:
                logger.exception(e)
                return e.response
        else:
            message = f"Error. Task definition already registered for challenge {challenge.pk}."
            return {
                "Error": message,
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            }
    else:
        message = (
            "Please ensure that the "
            "TASK_EXECUTION_ROLE_ARN is appropriately passed as an environment varible."
        )
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }


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
    service_name = f"{queue_name}_service"
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
        message = (
            f"Worker service for challenge {challenge.pk} already exists. "
            "Please scale, stop or delete."
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
    service_name = f"{queue_name}_service"
    task_def_arn = challenge.task_def_arn

    kwargs = update_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        task_def_arn=task_def_arn,
        force_new_deployment=force_new_deployment,
        num_of_tasks=num_of_tasks,
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
    service_name = f"{queue_name}_service"
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

    variables = {
        "AWS_ACCOUNT_ID": aws_keys["AWS_ACCOUNT_ID"],
        "AWS_ACCESS_KEY_ID": aws_keys["AWS_ACCESS_KEY_ID"],
        "AWS_SECRET_ACCESS_KEY": aws_keys["AWS_SECRET_ACCESS_KEY"],
        "AWS_REGION": aws_keys["AWS_REGION"],
        "PK": str(challenge.pk),
        "QUEUE": challenge.queue,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "CUSTOM_WORKER_IMAGE": challenge.worker_image_url,
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
            response = f"Please scale to a different number. Challenge has {num_of_tasks} worker(s)."
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


def scale_resources(challenge, worker_cpu_cores, worker_memory):
    """
    The function called by scale_resources_by_challenge_pk to send the AWS ECS request to update the resources used by
    a challenge's workers.

    Deregisters the old task definition and creates a new definition that is substituted into the challenge workers.

    Parameters:
    challenge (): The challenge object for whom the task definition is being registered.
    worker_cpu_cores (int): vCPU (1 CPU core = 1024 vCPU) that should be assigned to workers.
    worker_memory (int): The amount of memory (MB) that should be assigned to each worker.

    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """

    from .utils import get_aws_credentials_for_challenge

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

    try:
        response = client.deregister_task_definition(
            taskDefinition=challenge.task_def_arn
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.task_def_arn = None
            challenge.save()
    except ClientError as e:
        e.response["Error"] = True
        e.response["Message"] = "Scaling inactive workers not supported"
        logger.exception(e)
        return e.response

    if challenge.worker_image_url:
        updated_settings = {
            **COMMON_SETTINGS_DICT,
            "WORKER_IMAGE": challenge.worker_image_url,
        }
    else:
        updated_settings = COMMON_SETTINGS_DICT

    queue_name = challenge.queue
    container_name = f"worker_{queue_name}"
    log_group_name = get_log_group_name(challenge.pk)
    challenge_aws_keys = get_aws_credentials_for_challenge(challenge.pk)
    task_def = task_definition.format(
        queue_name=queue_name,
        container_name=container_name,
        ENV=ENV,
        challenge_pk=challenge.pk,
        CPU=worker_cpu_cores,
        MEMORY=worker_memory,
        ephemeral_storage=challenge.ephemeral_storage,
        log_group_name=log_group_name,
        AWS_SES_REGION_NAME=settings.AWS_SES_REGION_NAME,
        AWS_SES_REGION_ENDPOINT=settings.AWS_SES_REGION_ENDPOINT,
        **updated_settings,
        **challenge_aws_keys,
    )
    task_def = eval(task_def)

    try:
        response = client.register_task_definition(**task_def)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.worker_cpu_cores = worker_cpu_cores
            challenge.worker_memory = worker_memory
            task_def_arn = response["taskDefinition"]["taskDefinitionArn"]

            challenge.task_def_arn = task_def_arn
            challenge.save()
            force_new_deployment = False
            service_name = f"{queue_name}_service"
            num_of_tasks = challenge.workers
            kwargs = update_service_args.format(
                CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
                service_name=service_name,
                task_def_arn=task_def_arn,
                num_of_tasks=num_of_tasks,
                force_new_deployment=force_new_deployment,
            )
            kwargs = eval(kwargs)
            response = client.update_service(**kwargs)
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
        if (
            challenge.is_docker_based
            and not challenge.is_static_dataset_code_upload
        ):
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

    prev = getattr(instance, f"_original_{field_name}")
    curr = getattr(instance, f"{field_name}")

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
            f"The worker service for challenge {challenge.pk} was restarted, "
            f"as {field_name} was changed."
        )

        if count != 1:
            logger.warning(
                f"Worker(s) for challenge {challenge.id} couldn't restart! "
                f"Error: {failures[0]['message']}"
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

            # Update CloudWatch log retention policy on restart
            update_challenge_log_retention_on_restart(challenge)


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
        challenge_obj.title.replace(" ", "-")[:20], environment_suffix
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

            # Update CloudWatch log retention policy on approval
            update_challenge_log_retention_on_approval(challenge)

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


def calculate_retention_period_days(challenge_end_date):
    """
    Calculate retention period in days based on challenge end date.

    Args:
        challenge_end_date (datetime): The end date of the challenge phase

    Returns:
        int: Number of days for retention (30 days after challenge ends)
    """
    from django.utils import timezone

    now = timezone.now()
    if challenge_end_date > now:
        # Challenge is still active, retain until end date + 30 days
        days_until_end = (challenge_end_date - now).days
        return days_until_end + 30
    else:
        # Challenge has ended, retain for 30 more days
        days_since_end = (now - challenge_end_date).days
        return max(30 - days_since_end, 1)  # At least 1 day


def map_retention_days_to_aws_values(days):
    """
    Map retention period in days to valid AWS CloudWatch retention values.

    Args:
        days (int): Desired retention period in days

    Returns:
        int: Valid AWS CloudWatch retention period
    """
    # AWS CloudWatch valid retention periods (in days)
    valid_periods = [
        1,
        3,
        5,
        7,
        14,
        30,
        60,
        90,
        120,
        150,
        180,
        365,
        400,
        545,
        731,
        1827,
        3653,
    ]

    # Find the closest valid period that's >= requested days
    for period in valid_periods:
        if period >= days:
            return period

    # If requested days exceed maximum, use maximum
    return valid_periods[-1]


def set_cloudwatch_log_retention(challenge_pk, retention_days=None):
    """
    Set CloudWatch log retention policy for a challenge's log group.

    Args:
        challenge_pk (int): Challenge primary key
        retention_days (int, optional): Retention period in days. If None, calculates based on challenge end date.

    Returns:
        dict: Response containing success/error status
    """
    from .models import ChallengePhase
    from .utils import get_aws_credentials_for_challenge

    try:
        # Get challenge phases to determine end date
        phases = ChallengePhase.objects.filter(challenge_id=challenge_pk)
        if not phases.exists():
            return {"error": f"No phases found for challenge {challenge_pk}"}

        # Get the latest end date from all phases
        latest_end_date = max(
            phase.end_date for phase in phases if phase.end_date
        )

        if retention_days is None:
            retention_days = calculate_retention_period_days(latest_end_date)

        # Map to valid AWS retention period
        aws_retention_days = map_retention_days_to_aws_values(retention_days)

        # Get log group name
        log_group_name = get_log_group_name(challenge_pk)

        # Get AWS credentials for the challenge
        challenge_aws_keys = get_aws_credentials_for_challenge(challenge_pk)

        # Set up CloudWatch Logs client
        logs_client = get_boto3_client("logs", challenge_aws_keys)

        # Set retention policy
        logs_client.put_retention_policy(
            logGroupName=log_group_name, retentionInDays=aws_retention_days
        )

        logger.info(
            f"Set CloudWatch log retention for challenge {challenge_pk} "
            f"to {aws_retention_days} days"
        )

        return {
            "success": True,
            "retention_days": aws_retention_days,
            "log_group": log_group_name,
            "message": f"Retention policy set to {aws_retention_days} days",
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "ResourceNotFoundException":
            return {
                "error": f"Log group not found for challenge {challenge_pk}",
                "log_group": get_log_group_name(challenge_pk),
            }
        else:
            logger.exception(
                f"Failed to set log retention for challenge {challenge_pk}"
            )
            return {"error": str(e)}
    except Exception as e:
        logger.exception(
            f"Unexpected error setting log retention for challenge {challenge_pk}"
        )
        return {"error": str(e)}


def calculate_submission_retention_date(challenge_phase):
    """
    Calculate when a submission becomes eligible for retention cleanup.

    Args:
        challenge_phase: ChallengePhase object

    Returns:
        datetime: Date when submission artifacts can be deleted
    """
    from datetime import timedelta

    if not challenge_phase.end_date:
        return None

    # Only trigger retention if phase is not public (not accepting submissions)
    if challenge_phase.is_public:
        return None

    # 30 days after challenge phase ends
    return challenge_phase.end_date + timedelta(days=30)


def delete_submission_files_from_storage(submission):
    """
    Delete submission files from S3 storage while preserving database records.

    Args:
        submission: Submission object

    Returns:
        dict: Result of deletion operation
    """
    from .utils import get_aws_credentials_for_challenge

    deleted_files = []
    failed_files = []

    try:
        challenge_pk = submission.challenge_phase.challenge.pk
        challenge_aws_keys = get_aws_credentials_for_challenge(challenge_pk)
        s3_client = get_boto3_client("s3", challenge_aws_keys)
        bucket_name = challenge_aws_keys["AWS_STORAGE_BUCKET_NAME"]

        # List of file fields to delete
        file_fields = [
            "input_file",
            "submission_input_file",
            "stdout_file",
            "stderr_file",
            "environment_log_file",
            "submission_result_file",
            "submission_metadata_file",
        ]

        for field_name in file_fields:
            file_field = getattr(submission, field_name, None)
            if file_field and file_field.name:
                try:
                    # Delete from S3
                    s3_client.delete_object(
                        Bucket=bucket_name, Key=file_field.name
                    )
                    deleted_files.append(file_field.name)

                    # Clear the file field in the database
                    file_field.delete(save=False)

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get(
                        "Code", "Unknown"
                    )
                    if (
                        error_code != "NoSuchKey"
                    ):  # Ignore if file doesn't exist
                        failed_files.append(
                            {"file": file_field.name, "error": str(e)}
                        )
                        logger.warning(
                            f"Failed to delete {file_field.name}: {e}"
                        )

        # Mark submission as having artifacts deleted
        from django.utils import timezone

        submission.is_artifact_deleted = True
        submission.artifact_deletion_date = timezone.now()
        submission.save(
            update_fields=["is_artifact_deleted", "artifact_deletion_date"]
        )

        logger.info(
            f"Deleted {len(deleted_files)} files for submission {submission.pk}"
        )

        return {
            "success": True,
            "deleted_files": deleted_files,
            "failed_files": failed_files,
            "submission_id": submission.pk,
        }

    except Exception as e:
        logger.exception(
            f"Error deleting files for submission {submission.pk}"
        )
        return {
            "success": False,
            "error": str(e),
            "submission_id": submission.pk,
        }


@app.task
def cleanup_expired_submission_artifacts():
    """
    Periodic task to clean up expired submission artifacts.
    This task should be run daily via Celery Beat.
    """
    from django.utils import timezone
    from jobs.models import Submission

    logger.info("Starting cleanup of expired submission artifacts")

    # Find submissions eligible for cleanup
    now = timezone.now()
    eligible_submissions = Submission.objects.filter(
        retention_eligible_date__lte=now, is_artifact_deleted=False
    ).select_related("challenge_phase__challenge")

    cleanup_stats = {
        "total_processed": 0,
        "successful_deletions": 0,
        "failed_deletions": 0,
        "errors": [],
    }

    if not eligible_submissions.exists():
        logger.info("No submissions eligible for cleanup")
        return cleanup_stats

    logger.info(
        f"Found {eligible_submissions.count()} submissions eligible for cleanup"
    )

    for submission in eligible_submissions:
        cleanup_stats["total_processed"] += 1

        try:
            result = delete_submission_files_from_storage(submission)
            if result["success"]:
                cleanup_stats["successful_deletions"] += 1
                logger.info(
                    f"Successfully cleaned up submission {submission.pk} from challenge {submission.challenge_phase.challenge.title}"
                )
            else:
                cleanup_stats["failed_deletions"] += 1
                cleanup_stats["errors"].append(
                    {
                        "submission_id": submission.pk,
                        "challenge_id": submission.challenge_phase.challenge.pk,
                        "error": result.get("error", "Unknown error"),
                    }
                )
                logger.error(
                    f"Failed to clean up submission {submission.pk}: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            cleanup_stats["failed_deletions"] += 1
            cleanup_stats["errors"].append(
                {
                    "submission_id": submission.pk,
                    "challenge_id": submission.challenge_phase.challenge.pk,
                    "error": str(e),
                }
            )
            logger.exception(
                f"Unexpected error cleaning up submission {submission.pk}"
            )

    logger.info(
        f"Cleanup completed. Processed: {cleanup_stats['total_processed']}, "
        f"Successful: {cleanup_stats['successful_deletions']}, "
        f"Failed: {cleanup_stats['failed_deletions']}"
    )

    # Log errors for monitoring
    if cleanup_stats["errors"]:
        logger.error(f"Cleanup errors: {cleanup_stats['errors']}")

    return cleanup_stats


@app.task
def update_submission_retention_dates():
    """
    Task to update retention eligible dates for submissions based on challenge phase end dates.
    This should be run when challenge phases are updated or periodically.
    """
    from challenges.models import ChallengePhase
    from jobs.models import Submission

    logger.info("Updating submission retention dates")

    updated_count = 0
    errors = []

    try:
        # Get all challenge phases that have ended and are not public
        ended_phases = ChallengePhase.objects.filter(
            end_date__isnull=False, is_public=False
        )

        if not ended_phases.exists():
            logger.info(
                "No ended challenge phases found - no retention dates to update"
            )
            return {"updated_submissions": 0, "errors": []}

        logger.info(
            f"Found {ended_phases.count()} ended challenge phases to process"
        )

        for phase in ended_phases:
            try:
                retention_date = calculate_submission_retention_date(phase)
                if retention_date:
                    # Update submissions for this phase
                    submissions_updated = Submission.objects.filter(
                        challenge_phase=phase,
                        retention_eligible_date__isnull=True,
                        is_artifact_deleted=False,
                    ).update(retention_eligible_date=retention_date)

                    updated_count += submissions_updated

                    if submissions_updated > 0:
                        logger.info(
                            f"Updated {submissions_updated} submissions for phase {phase.pk} "
                            f"({phase.challenge.title}) with retention date {retention_date}"
                        )
                else:
                    logger.debug(
                        f"No retention date calculated for phase {phase.pk} - phase may still be public"
                    )

            except Exception as e:
                error_msg = f"Failed to update retention dates for phase {phase.pk}: {str(e)}"
                logger.error(error_msg)
                errors.append(
                    {
                        "phase_id": phase.pk,
                        "challenge_id": phase.challenge.pk,
                        "error": str(e),
                    }
                )

    except Exception as e:
        error_msg = f"Unexpected error during retention date update: {str(e)}"
        logger.exception(error_msg)
        errors.append({"error": str(e)})

    logger.info(f"Updated retention dates for {updated_count} submissions")

    if errors:
        logger.error(f"Retention date update errors: {errors}")

    return {"updated_submissions": updated_count, "errors": errors}


@app.task
def send_retention_warning_notifications():
    """
    Send warning notifications to challenge hosts 14 days before retention cleanup.
    """
    from datetime import timedelta

    from django.utils import timezone
    from jobs.models import Submission

    logger.info("Checking for retention warning notifications")

    # Find submissions that will be cleaned up in 14 days
    warning_date = timezone.now() + timedelta(days=14)
    warning_submissions = Submission.objects.filter(
        retention_eligible_date__date=warning_date.date(),
        is_artifact_deleted=False,
    ).select_related("challenge_phase__challenge__creator")

    if not warning_submissions.exists():
        logger.info("No submissions require retention warning notifications")
        return {"notifications_sent": 0}

    logger.info(
        f"Found {warning_submissions.count()} submissions requiring retention warnings"
    )

    # Group by challenge to send one email per challenge
    challenges_to_notify = {}
    for submission in warning_submissions:
        challenge = submission.challenge_phase.challenge
        if challenge.pk not in challenges_to_notify:
            challenges_to_notify[challenge.pk] = {
                "challenge": challenge,
                "submission_count": 0,
            }
        challenges_to_notify[challenge.pk]["submission_count"] += 1

    notifications_sent = 0
    notification_errors = []

    for challenge_data in challenges_to_notify.values():
        challenge = challenge_data["challenge"]
        submission_count = challenge_data["submission_count"]

        try:
            # Skip if challenge doesn't want host notifications
            if not challenge.inform_hosts:
                logger.info(
                    f"Skipping notification for challenge {challenge.pk} - inform_hosts is False"
                )
                continue

            # Send notification email to challenge hosts
            if (
                not hasattr(settings, "EVALAI_API_SERVER")
                or not settings.EVALAI_API_SERVER
            ):
                logger.error(
                    "EVALAI_API_SERVER setting is missing - cannot generate challenge URL"
                )
                continue

            challenge_url = f"{settings.EVALAI_API_SERVER}/web/challenges/challenge-page/{challenge.id}"

            template_data = {
                "CHALLENGE_NAME": challenge.title,
                "CHALLENGE_URL": challenge_url,
                "SUBMISSION_COUNT": submission_count,
                "RETENTION_DATE": warning_date.strftime("%B %d, %Y"),
                "DAYS_REMAINING": 14,
            }

            if challenge.image:
                template_data["CHALLENGE_IMAGE_URL"] = challenge.image.url

            # Get template ID from settings
            template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES", {}).get(
                "RETENTION_WARNING_EMAIL", None
            )

            if not template_id:
                logger.error(
                    "RETENTION_WARNING_EMAIL template ID not configured in settings"
                )
                continue

            # Get challenge host emails
            try:
                emails = challenge.creator.get_all_challenge_host_email()
                if not emails:
                    logger.warning(
                        f"No host emails found for challenge {challenge.pk}"
                    )
                    continue
            except Exception as e:
                logger.error(
                    f"Failed to get host emails for challenge {challenge.pk}: {e}"
                )
                continue

            # Send emails to all hosts
            email_sent = False
            for email in emails:
                try:
                    send_email(
                        sender=settings.CLOUDCV_TEAM_EMAIL,
                        recipient=email,
                        template_id=template_id,
                        template_data=template_data,
                    )
                    email_sent = True
                    logger.info(
                        f"Sent retention warning email to {email} for challenge {challenge.pk}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send retention warning email to {email} for challenge {challenge.pk}: {e}"
                    )
                    notification_errors.append(
                        {
                            "challenge_id": challenge.pk,
                            "email": email,
                            "error": str(e),
                        }
                    )

            if email_sent:
                notifications_sent += 1
                logger.info(
                    f"Sent retention warning for challenge {challenge.pk} ({submission_count} submissions)"
                )

        except Exception as e:
            logger.exception(
                f"Failed to send retention warning for challenge {challenge.pk}"
            )
            notification_errors.append(
                {"challenge_id": challenge.pk, "error": str(e)}
            )

    logger.info(f"Sent {notifications_sent} retention warning notifications")

    if notification_errors:
        logger.error(f"Notification errors: {notification_errors}")

    return {
        "notifications_sent": notifications_sent,
        "errors": notification_errors,
    }


def update_challenge_log_retention_on_approval(challenge):
    """
    Update CloudWatch log retention when a challenge is approved.
    Called from challenge_approval_callback.
    """
    if not settings.DEBUG:
        try:
            result = set_cloudwatch_log_retention(challenge.pk)
            if result.get("success"):
                logger.info(
                    f"Updated log retention for approved challenge {challenge.pk}"
                )
            else:
                logger.warning(
                    f"Failed to update log retention for challenge {challenge.pk}: {result.get('error')}"
                )
        except Exception as e:
            logger.exception(
                f"Error updating log retention for challenge {challenge.pk}"
            )


def update_challenge_log_retention_on_restart(challenge):
    """
    Update CloudWatch log retention when workers are restarted.
    Called from restart_workers_signal_callback.
    """
    if not settings.DEBUG:
        try:
            result = set_cloudwatch_log_retention(challenge.pk)
            if result.get("success"):
                logger.info(
                    f"Updated log retention for restarted challenge {challenge.pk}"
                )
        except Exception as e:
            logger.exception(
                f"Error updating log retention for restarted challenge {challenge.pk}"
            )


def update_challenge_log_retention_on_task_def_registration(challenge):
    """
    Update CloudWatch log retention when task definition is registered.
    Called from register_task_def_by_challenge_pk.
    """
    if not settings.DEBUG:
        try:
            result = set_cloudwatch_log_retention(challenge.pk)
            if result.get("success"):
                logger.info(
                    f"Updated log retention for challenge {challenge.pk} task definition"
                )
        except Exception as e:
            logger.exception(
                f"Error updating log retention for challenge {challenge.pk} task definition"
            )
