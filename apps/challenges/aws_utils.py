import os
import random
import string
import logging

from botocore.exceptions import ClientError
from base.utils import get_boto3_client

from http import HTTPStatus

logger = logging.getLogger(__name__)


DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
ENV = DJANGO_SETTINGS_MODULE.split(".")[-1]
aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
}

TASK_ROLE_ARN =  os.environ.get("TASK_ROLE_ARN", ""),
TASK_EXECUTION_ROLE_ARN = os.environ.get("TASK_EXECUTION_ROLE_ARN", "")


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
            "repositoryCredentials": {{
                "credentialsParameter": ""
            }},
            "portMappings": [
                {{
                    "containerPort": 0,
                }}
            ],
            "essential": True,
            "environment": [
                {{
                    "name": "PYTHONUNBUFFERED",
                    "value": "1"
                }},
                {{  # If we pass here, they are visible on console.
                    "name": "AWS_DEFAULT_REGION",
                    "value": "{AWS_DEFAULT_REGION}"
                }},
                {{
                    "name": "DJANGO_SERVER",
                    "value": "django"
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
            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-create-group": "true",
                    "awslogs-region": "us-east-1",
                    "awslogs-group": "{log_group}",
                    "awslogs-stream-prefix": "{queue_name}"  # log stream format: prefix-name/container-name/ecs-task-id
                }},
            }},
            "healthCheck": {{
                "command": [  # Need healthcheck command.
                    ""
                ],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 0
            }},
        }}
    ],
    "requiresCompatibilities":[
        "FARGATE"
    ],
    "cpu":"",  # Need hard limits.
    "memory":"",
}}
"""

service_definition = """
{{
    "cluster":"Challenge_Cluster",
    "serviceName":"{service_name}",
    "taskDefinition":"{task_def_arn}",
    "desiredCount":1,
    "clientToken":"{client_token}",
    "launchType":"FARGATE",
    "platformVersion":"LATEST",
    "networkConfiguration":{{ # Need to create VPC before filling this.
        "awsvpcConfiguration": {{
            "subnets": [
                # "string",
            ],
            'securityGroups': [
                "string",
            ],
            "assignPublicIp": "ENABLED"
        }}
    }},
    "healthCheckGracePeriodSeconds":30,
    "schedulingStrategy":"REPLICA",
    "deploymentController":{{
        "type": "ECS"
    }},
    "enableECSManagedTags":True,
    "propagateTags":"SERVICE"
}}
"""

update_service_args = """
{{
    "cluster":"Challenge_Cluster",
    "service":"{service_name}",
    "desiredCount":num_of_tasks,
    "taskDefinition":"{task_def_arn}",
    "forceNewDeployment":False
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
                                            challenge_pk=challenge.pk, log_group=log_group)
        definition = eval(definition)
        if challenge.task_def_arn is "":
            try:
                response = client.register_task_definition(**definition)
                return response
            except ClientError as e:
                logger.info(e)
                return e.response
        else:
            message = "Error. Task definition already registered for challenge {}.".format(challenge.pk)
            return {"Error": message, "ResponseMetadata": {"HTTPStatusCode": None}}
    else:
        message = "Please ensure that the TASK_ROLE_ARN & TASK_EXECUTION_ROLE_ARN are appropriately passed as environment varibles."
        return {"Error": message, "ResponseMetadata": {"HTTPStatusCode": None}}


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
        if (response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK):
            task_def_arn = response["taskDefinition"]["taskDefinitionArn"]
            challenge.task_def_arn = task_def_arn
            challenge.save()
        else:
            return response
        definition = service_definition.format(service_name=service_name, task_def_arn=task_def_arn, client_token=client_token)
        definition = eval(definition)
        try:
            response = client.create_service(**definition)
            return response
        except ClientError as e:
            return e.response
    else:
        message = "Worker service for challenge {} already exists. Please scale, stop or delete.".format(challenge.pk)
        return {"Error": message, "ResponseMetadata": {"HTTPStatusCode": None}}


def update_service_by_challenge_pk(client, challenge, num_of_tasks):
    """
    Registers the task definition of the worker for a challenge, before creating a service.

    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    queue_name (str): queue_name is the queue field of the Challenge model used in many parameters fof the task def.
    challenge (<class 'challenges.models.Challenge'>): The challenge object for whom the task definition is being registered.

    Returns:
    dict: The response returned by the update_service method from boto3
    """

    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    task_def_arn = challenge.task_def_arn

    definition = update_service_args.format(service_name=service_name, task_def_arn=task_def_arn)
    definition = eval(definition)

    try:
        response = client.update_service(**definition)
        return response
    except ClientError as e:
        return e.response


def service_manager(client, challenge, num_of_tasks=None):
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
        response = update_service_by_challenge_pk(client, challenge, num_of_tasks)
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

    ecs = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (challenge.workers == 0) or (challenge.workers is None):
            response = service_manager(client=ecs, challenge=challenge, num_of_tasks=1)
            if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
                return {"count": count, "message": response['Error']}
            count += 1
        else:
            response = {"Error": "Please select only inactive challenges."}
            return {"count": count, "message": response}
    message = "All selected workers successfully started."
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

    ecs = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(client=ecs, challenge=challenge, num_of_tasks=0)
            if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
                return {"count": count, "message": response['Error']}
            count += 1
        else:
            response = {"Error": "Please select only active challenges."}
            return {"count": count, "message": response}
    message = "All selected workers successfully stopped."
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

    ecs = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (num_of_tasks == challenge.workers):
            message = "Please scale to a different number than current worker count for challenge {}".format(challenge.pk)
            return {"count": count, "message": message}
        response = service_manager(client=ecs, challenge=challenge, num_of_tasks=num_of_tasks)
        if (response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK):
            return {"count": count, "message": response['Error']}
        count += 1
    message = "All selected workers successfully scaled."
    return {"count": count, "message": message}
