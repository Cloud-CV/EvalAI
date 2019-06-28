import os
import random
import string
import logging

from botocore.exceptions import ClientError
from base.utils import get_boto3_client

logger = logging.getLogger(__name__)

"""
The 3 strings below are converted to dictionaries and passed as keword args to the respective
boto3 methods.
"""
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
                    "value": "settings.prod"
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

aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
}


def client_token_generator():
    client_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    return client_token

"""
Called by: create_service_by_challenge_pk (below).

Registers the task definition for a new challenge, and raises a custom exception
if the worker service is already active (which is caught by the create_service custom method.).
"""


def register_task_def_by_challenge_pk(client, queue_name, challenge):
    container_name = "worker_{}".format(queue_name)
    image = "{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-production-worker:latest".format(AWS_ACCOUNT_ID=aws_keys["AWS_ACCOUNT_ID"])
    AWS_DEFAULT_REGION = aws_keys["AWS_REGION"]
    log_group = "{}_logs".format(queue_name)

    task_role_arn = os.environ.get("TASK_ROLE_ARN", "")
    execution_role_arn = os.environ.get("TASK_EXECUTION_ROLE_ARN", "")

    definition = task_definition.format(queue_name=queue_name, task_role_arn=task_role_arn,
                                        execution_role_arn=execution_role_arn, container_name=container_name,
                                        image=image, AWS_DEFAULT_REGION=AWS_DEFAULT_REGION,
                                        challenge_pk=challenge.pk, log_group=log_group)
    definition = eval(definition)
    if challenge.task_def_arn is "":
        try:
            response = client.register_task_definition(**definition)
            task_def_arn = response["taskDefinition"].get("taskDefinitionArn")
            challenge.task_def_arn = task_def_arn
            challenge.save()
            return task_def_arn
        except Exception as e:
            logger.info(e)
            raise
    error = "Error. Task definition already registered for challenge {}.".format(challenge.pk)
    raise Exception(error)


# Called by the service_manager.
def create_service_by_challenge_pk(client, challenge, client_token):
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    if challenge.workers is None:  # Verify if the challenge is new (i.e, service not yet created.).
        try:
            task_def_arn = register_task_def_by_challenge_pk(client, queue_name, challenge)
        except Exception as e:
            return e.response["Error"]

        definition = service_definition.format(service_name=service_name, task_def_arn=task_def_arn, client_token=client_token)
        definition = eval(definition)
        try:
            response = client.create_service(**definition)
            # To verify if the service has been created on AWS.
            if (response["ResponseMetadata"]["HTTPStatusCode"] == 200) and (response["service"]["serviceName"] == service_name):
                challenge.workers = 1
                challenge.save()
                message = {"Success": "Service created succesfully."}
                return message
            return "Creation for challenge {}.".format(challenge.pk)
        except ClientError as e:
                return e.response["Error"]
    return "Worker service for challenge {} already exists. Please scale, stop or delete.".format(challenge.pk)


# Called by the service_manager.
def update_service_by_challenge_pk(client, challenge, num_of_tasks):
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    task_def_arn = challenge.task_def_arn

    definition = update_service_args.format(service_name=service_name, task_def_arn=task_def_arn)
    definition = eval(definition)

    try:
        response = client.update_service(**definition)
        # To verify if the service has been updated on AWS.
        if (response["ResponseMetadata"]["HTTPStatusCode"] == 200) and (response["service"]["serviceName"] == service_name):
            challenge.workers = num_of_tasks
            challenge.save()
            message = {"Success": "Service updated succesfully."}
            return message
        return "Update failed for challenge {}.".format(challenge.pk)
    except ClientError as e:
        return e.response['Error']

"""
Called by: Start, Stop & Scale methods for multiple workers. (Below)

This method determines if the challenge is new or not, and accordingly
calls the create or update custom method.
"""


def service_manager(client, challenge, num_of_tasks=None):
    if challenge.workers is not None:
        response = update_service_by_challenge_pk(client, challenge, num_of_tasks)
        return response
    else:
        client_token = client_token_generator()
        response = create_service_by_challenge_pk(client, challenge, client_token)
        return response

"""
The 3 functions below are used directly in the admin action methods and the response returned by
these are displayed as success or error messages on the admin page

Called by: their respective admin action methods in apps/challenges/admin.py.
"""


def start_workers(queryset):
    ecs = get_boto3_client("ecs", aws_keys)
    count = 0   # Num of succesful starts.
    for challenge in queryset:
        if (challenge.workers == 0) or (challenge.workers is None):  # To verify if the challenge is inactive or new.
            response = service_manager(client=ecs, challenge=challenge, num_of_tasks=1)
            if "Success" not in response:
                # This response is formatted in the admin page to give 2 messages
                # 1)Num of succesful starts before error. 2)The error if any for the first failure.
                return {"count": count, "message": response}
            count += 1
        else:
            response = {"Error": "Please select only inactive workers."}
            return {"count": count, "message": response}
    message = "{} workers were succesfully started.".format(count)
    return {"count": count, "message": message}


def stop_workers(queryset):
    ecs = get_boto3_client("ecs", aws_keys)
    count = 0
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):  # To verify if the challenge is not new and active.
            response = service_manager(client=ecs, challenge=challenge, num_of_tasks=0)
            if "Success" not in response:
                # This response is formatted in the admin page to give 2 messages
                # 1)Num of succesful stops before error. 2)The error if any for the first failure.
                return {"count": count, "message": response}
            count += 1
        else:
            response = {"Error": "Please select running workers."}
            return {"count": count, "message": response}
    message = "{} workers were succesfully stopped.".format(count)
    return {"count": count, "message": message}


def scale_workers(queryset, num_of_tasks):
    ecs = get_boto3_client("ecs", aws_keys)
    count = 0  # Num of succesful scales.
    for challenge in queryset:
        if(num_of_tasks == challenge.workers):  # To check if target number is same as current.
            return {"count": count, "message": "Please scale to a different number than current worker count."}
        response = service_manager(client=ecs, challenge=challenge, num_of_tasks=num_of_tasks)
        if "Success" not in response:
            # This response is formatted in the admin page to give 2 messages
            # 1)Num of succesful stops before error. 2)The error if any for the first failure.
            return {"count": count, "message": response}
        count += 1
    message = "{} workers were succesfully scaled.".format(count)
    return {"count": count, "message": message}
