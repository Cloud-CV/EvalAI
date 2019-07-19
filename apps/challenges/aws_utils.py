import logging
import os
import random
import string

from botocore.exceptions import ClientError
from django.conf import settings
from http import HTTPStatus
from moto import mock_ecs

from base.utils import get_boto3_client


logger = logging.getLogger(__name__)


DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
ENV = DJANGO_SETTINGS_MODULE.split(".")[-1]
aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
}

TASK_ROLE_ARN = os.environ.get("TASK_ROLE_ARN", ""),
TASK_EXECUTION_ROLE_ARN = "arn:aws:iam::{}:role/evalaiTaskExecutionRole".format(aws_keys["AWS_ACCOUNT_ID"])

DJANGO_SETTINGS_DICT = {
    "DJANGO_SERVER": os.environ.get("DJANGO_SERVER", "localhost")
    "DEBUG": settings.DEBUG
    "EMAIL_HOST": os.environ.get("EMAIL_HOST", "https://email_host"),
    "EMAIL_HOST_PASSWORD": os.environ.get("EMAIL_HOST_PASSWORD", "x"),
    "EMAIL_HOST_USER":os.environ.get("EMAIL_HOST_USER", "user"),
    "EMAIL_PORT": os.environ.get("EMAIL_PORT", 587),
    "EMAIL_USE_TLS": os.environ.get("EMAIL_USE_TLS", "True"),
    "MEMCACHED_LOCATION": os.environ.get("MEMCACHED_LOCATION", "None"),
    "RDS_DB_NAME": os.environ.get("RDS_DB_NAME", "rds_db"),
    "RDS_HOSTNAME": os.environ.get("RDS_HOSTNAME", "rds_host"),
    "RDS_PASSWORD": os.environ.get("RDS_PASSWORD", "x"),
    "RDS_USERNAME": os.environ.get("RDS_USERNAME", "user"),
    "SECRET_KEY": os.environ.get("SECRET_KEY", "x"),
    "SENTRY_URL": os.environ.get("SENTRY_URL", "https://sentry_url"),
}

task_definition = """
{{
    "family":"{queue_name}",
    "taskRoleArn":"{task_role_arn}",
    "executionRoleArn":"{execution_role_arn}",
    "networkMode":"awsvpc",
    "containerDefinitions":[
        {{
            "name": "{container_name}",
            "image": "{image}",
            "essential": True,
            "environment": [
                {{
                    "name": "PYTHONUNBUFFERED",
                    "value": "1"
                }},
                {{
                    "name": "AWS_DEFAULT_REGION",
                    "value": "{AWS_DEFAULT_REGION}"
                }},
                {{
                    "name": "DJANGO_SERVER",
                    "value": "{DJANGO_SERVER}"
                }},
                {{
                    "name": "DJANGO_SETTINGS_MODULE",
                    "value": "settings.{env}"
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
                  "name": "SECRET_KEY",
                  "value": "{SECRET_KEY}"
                }},
                {{
                  "name": "SENTRY_URL",
                  "value": "{SENTRY_URL}"
                }},
            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-create-group": "true",
                    "awslogs-group": "gsoc2019",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "{queue_name}",
                }},
            }},
        }}
    ],
    "requiresCompatibilities":[
        "FARGATE"
    ],
    "cpu": "1024",
    "memory": "2048",
}}
"""

service_definition = """
{{
    "cluster":"gsoc2019",
    "serviceName":"{service_name}",
    "taskDefinition":"{task_def_arn}",
    "desiredCount":1,
    "clientToken":"{client_token}",
    "launchType":"FARGATE",
    "platformVersion":"LATEST",
    "networkConfiguration":{{
        "awsvpcConfiguration": {{
            "subnets": [
                "subnet-e260d5be",
                "subnet-300ea557",
            ],
            'securityGroups': [
                "sg-148b4a5e",
            ],
            "assignPublicIp": "ENABLED"
        }}
    }},
    "schedulingStrategy":"REPLICA",
    "deploymentController":{{
        "type": "ECS"
    }},
}}
"""

update_service_args = """
{{
    "cluster":"gsoc2019",
    "service":"{service_name}",
    "desiredCount":num_of_tasks,
    "taskDefinition":"{task_def_arn}",
    "forceNewDeployment":{forceNewDeployment}
}}
"""

delete_service_args = """
{{
    "cluster": "gsoc2019",
    "service": "{service_name}",
    "force": False
}}
"""


def client_token_generator():
    """
    Returns a 32 characters long client token to ensure idempotency with create_service boto3 requests.

    Parameters: None

    Returns:
    str: string of size 32 composed of digits and letters
    """

    client_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
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
    image = "{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-{env}-worker:latest".format(AWS_ACCOUNT_ID=aws_keys["AWS_ACCOUNT_ID"], env=ENV)
    AWS_DEFAULT_REGION = aws_keys["AWS_REGION"]
    log_group = "{}_logs".format(queue_name)

    task_role_arn = TASK_ROLE_ARN
    execution_role_arn = TASK_EXECUTION_ROLE_ARN

    if task_role_arn and execution_role_arn:
        definition = task_definition.format(queue_name=queue_name, task_role_arn=task_role_arn,
                                            execution_role_arn=execution_role_arn, container_name=container_name,
                                            image=image, AWS_DEFAULT_REGION=AWS_DEFAULT_REGION, env=ENV,
                                            challenge_pk=challenge.pk, log_group=log_group, **DJANGO_SETTINGS_DICT)
        definition = eval(definition)
        if not challenge.task_def_arn:
            try:
                response = client.register_task_definition(**definition)
                if (response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK):
                    task_def_arn = response["taskDefinition"]["taskDefinitionArn"]
                    challenge.task_def_arn = task_def_arn
                    challenge.save()
                return response
            except ClientError as e:
                logger.info(e)
                return e.response
        else:
            message = "Error. Task definition already registered for challenge {}.".format(challenge.pk)
            return {"Error": message, "ResponseMetadata": {"HTTPStatusCode": 400}}
    else:
        message = "Please ensure that the TASK_ROLE_ARN & TASK_EXECUTION_ROLE_ARN are appropriately passed as environment varibles."
        return {"Error": message, "ResponseMetadata": {"HTTPStatusCode": 400}}


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
    if challenge.workers is None:  # Verify if the challenge is new (i.e, service not yet created.).
        response = register_task_def_by_challenge_pk(client, queue_name, challenge)
        if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
            return response
        task_def_arn = challenge.task_def_arn
        definition = service_definition.format(service_name=service_name, task_def_arn=task_def_arn, client_token=client_token)
        definition = eval(definition)
        try:
            response = client.create_service(**definition)
            if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
                challenge.workers = 1
                challenge.save()
            return response
        except ClientError as e:
            return e.response
    else:
        message = "Worker service for challenge {} already exists. Please scale, stop or delete.".format(challenge.pk)
        return {"Error": message, "ResponseMetadata": {"HTTPStatusCode": 400}}


def update_service_by_challenge_pk(client, challenge, num_of_tasks, forceNewDeployment=False):
    """
    Updates the worker service for a challenge, and scales the number of workers to num_of_tasks.

    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>): The challenge object  for whom the task definition is being registered.
    num_of_tasks (int): Number of workers to scale to for the challenge.
    forceNewDeployment (bool): Set True (mainly for restarting) to specify if you want to redploy with the latest image from ECR. Default is False.

    Returns:
    dict: The response returned by the update_service method from boto3. If unsuccesful, returns an error dictionary
    """

    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    task_def_arn = challenge.task_def_arn

    kwargs = update_service_args.format(service_name=service_name, task_def_arn=task_def_arn, forceNewDeployment=forceNewDeployment)
    kwargs = eval(kwargs)

    try:
        response = client.update_service(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = num_of_tasks
            challenge.save()
        return response
    except ClientError as e:
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
    if(ENV is "dev"):
        mock = mock_ecs()
        mock.start()

    client = get_boto3_client("ecs", aws_keys)
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    kwargs = delete_service_args.format(service_name=service_name, force=True)
    kwargs = eval(kwargs)
    try:
        if(challenge.workers != 0):
            response = update_service_by_challenge_pk(client, challenge, 0, False)
            if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
                return response

        client.deregister_task_definition(taskDefinition=challenge.task_def_arn)
        response = client.delete_service(**kwargs)
        if(ENV is "dev"):
            mock.stop()
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = None
            challenge.task_def_arn = ""
            challenge.save()
        return response
    except ClientError as e:
            return e.response


def service_manager(client, challenge, num_of_tasks=None, forceNewDeployment=False):
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
        response = update_service_by_challenge_pk(client, challenge, num_of_tasks, forceNewDeployment)
        return response
    else:
        client_token = client_token_generator()
        response = create_service_by_challenge_pk(client, challenge, client_token)
        return response


def start_workers(queryset):
    """
    The function called by the admin action method to start all the selected workers.

    Calls the service_manager method. Before calling, checks if all the workers are incactive.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'message': the message to be displayed on the django admin page
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (challenge.workers == 0) or (challenge.workers is None):
            response = service_manager(client, challenge=challenge, num_of_tasks=1)
            if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
                return {"count": count, "message": response['Error']}
            count += 1
        else:
            response = "Please select only inactive challenges."
            return {"count": count, "message": response}
    message = "All selected challenge workers successfully started."
    return {"count": count, "message": message}


def stop_workers(queryset):
    """
    The function called by the admin action method to stop all the selected workers.

    Calls the service_manager method. Before calling, verifies that the challenge is not new, and is active.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'message': the message to be displayed on the django admin page
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(client, challenge=challenge, num_of_tasks=0)
            if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
                return {"count": count, "message": response['Error']}
            count += 1
        else:
            response = "Please select only active challenges."
            return {"count": count, "message": response}
    message = "All selected challenge workers successfully stopped."
    return {"count": count, "message": message}


def scale_workers(queryset, num_of_tasks):
    """
    The function called by the admin action method to scale all the selected workers.

    Calls the service_manager method. Before calling, checks if the target scaling number is different than current.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'message': the message to be displayed on the django admin page
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if not challenge.workers:
            response = "Please start worker for Challenge {} before scaling.".format(challenge.pk)
            return {"count": count, "message": response}
        if (num_of_tasks == challenge.workers):
            response = "Please scale to a different number. Challenge {} has {} workers.".format(challenge.pk, num_of_tasks)
            return {"count": count, "message": response}
        response = service_manager(client, challenge=challenge, num_of_tasks=num_of_tasks)
        if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
            return {"count": count, "message": response}
        count += 1
    message = "All selected challenge workers successfully scaled."
    return {"count": count, "message": message}


def delete_workers(queryset):
    """
    The function called by the admin action method to delete all the selected workers.

    Calls the delete_service_by_challenge_pk method. Before calling, verifies that the challenge is not new.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'message': the message to be displayed on the django admin page
    """
    count = 0
    for challenge in queryset:
        if challenge.workers is not None:
            response = delete_service_by_challenge_pk(challenge=challenge)
        else:
            response = "Please select only active challenges. Challenge {} is inactive.".format(challenge.pk)
            return {"count": count, "message": response}

        if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
            return {"count": count, "message": response['Error']}
        count += 1
    message = "All selected challenge workers successfully deleted."
    return {"count": count, "message": message}


def restart_workers(queryset):
    """
    The function called by the admin action method to restart all the selected workers.

    Calls the delete_service_by_challenge_pk method. Before calling, verifies that the challenge worker(s) is(are) active.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'message': the message to be displayed on the django admin page
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(client, challenge, num_of_tasks=challenge.workers, forceNewDeployment=True)
        else:
            response = "Please select only active challenges. Challenge {} is inactive.".format(challenge.pk)
            return {"count": count, "message": response}

        if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
            return {"count": count, "message": response['Error']}
        count += 1
    message = "All selected challenge workers successfully restarted."
    return {"count": count, "message": message}


def restart_workers_signal_callback(sender, instance, field_name, **kwargs):
    """
    Called when either evaluation_script or test_annotation_script for challenge
    is updated, to restart the challenge workers.
    """
    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))
    if prev != curr:
        if(field_name == "test_annotation"):
            challenge = instance.challenge
        else:
            challenge = instance
        restart_workers([challenge])
        logger.info("The worker service for challenge {} was restarted.".format(instance.pk))
