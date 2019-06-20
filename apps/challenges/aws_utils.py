import boto3
from botocore.exceptions import ClientError
import os
import random
from .models import Challenge
from .views import(
    get_broker_url_by_challenge_pk,
    get_broker_urls
)

from base.utils import get_boto3_client


task_definition = """
[
    "family":"",
    "taskRoleArn":"",  # Used by the container itself. (Not needed if passing env vars)
    "executionRoleArn":"",  # Used by the container agent. Also used for logs.
    "networkMode":"awsvpc",
    "containerDefinitions":[
        {
            "name": "{container_name}",
            "image": "{image}",
            "repositoryCredentials": {
                "credentialsParameter": ""
            },
            "memoryReservation": 0,  # in MiB
            "portMappings": [
                {
                    "containerPort": 0, # Might use this for healthcheck (?)
                }
            ],
            "essential": true,
            "environment": [
                {  # Not req I think, because used in dockerfile 
                   # already & image is already built.
                    "name": "PYTHONUNBUFFERED",
                    "value": "1"
                },
                {  # If we pass here, they are visible on console.
                    "name": "AWS_DEFAULT_REGION",
                    "value": "{AWS_DEFAULT_REGION}" # This still needs to be passed as env var?
                },
                {
                    "name": "DJANGO_SERVER",
                    "value": "django"
                },
                {
                    "name": "DJANGO_SETTINGS_MODULE",
                    "value": "settings.prod"
                },
                {
                    "name": "CHALLENGE_PK",
                    "value": "{challenge_pk}"
                },
                {
                    "name": "CHALLENGE_QUEUE",
                    "value": "{queue_name}"
                },
            ],
            "secrets": [  # use this for passing env vars? No.
                {
                    "name": "",
                    "valueFrom": ""
                }
            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": false,
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-create-group": true,
                    # Your IAM policy must include the logs:CreateLogGroup permission
                    # before you attempt to use awslogs-create-group.
                    "awslogs-region": "us-east-1",
                    "awslogs-group": "{log_group}",
                    "awslogs-stream-prefix": "{queue_name}"  
                    # log stream format: prefix-name/container-name/ecs-task-id
                },
            },
            "healthCheck": {
                "command": [
                    ""
                ],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 0
            },
            "resourceRequirements": [  # Not required I think. 
                                       # We're not gonna use GPUs.
                {
                    "value": "",
                    "type": "GPU"
                }
            ]
        }
    ],
    "requiresCompatibilities":[
        "FARGATE"
    ],
    "cpu":"",  # Hard limits
    "memory":"",
]
"""

service_definition = """
[
    cluster:'Challenge_Cluster',
    serviceName:'{service_name}',
    taskDefinition:'{task_def_arn}',
    loadBalancers:[  # Gotta create an application load balancer through boto3. Not even required right?
                     # Not required since no incoming reqs. But needed for outgoing evalai API calls?
        {
            'targetGroupArn': 'string',
            'loadBalancerName': 'string',
            'containerName': 'string',
            'containerPort': 123
        },
    ],
    desiredCount:1,
    clientToken:'{client_token}',
    launchType='FARGATE',
    platformVersion:'LATEST',
    role:'string',  # if and only if using a load balancer. 
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': [
                'string',
            ],
            'securityGroups': [
                'string',
            ],
            'assignPublicIp': 'ENABLED'
        }
    },
    healthCheckGracePeriodSeconds:30,
    schedulingStrategy"'REPLICA',
    deploymentController={
        'type': 'ECS'  
    },
    enableECSManagedTags:True,
    propagateTags"'SERVICE'
}
"""

aws_keys = {
            "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID"),
            "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        }

def client_token_generator():
    client_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    return client_token

def worker_scaling_callback(sender, instance, **kwargs):
    if not (getattr(instance, "_original_workers") == instance.workers):
        if (getattr(instance, "scaling_action")):  # Change the flag to true in the admin action method or the view the form redirects to & back to false at end of this method.
            num_of_tasks = instance.workers
            service_manager(challenge=instance, num_of_tasks=num_of_tasks)
            instance.scaling_action = False

def register_task_def_by_challenge_pk(client, queue_name, challenge_pk):
    container_name = "worker_{}".format(queue_name)
    image = "{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-production-worker:latest".format(AWS_ACCOUNT_ID=os.environ.get("AWS_ACCOUNT_ID"))
    AWS_DEFAULT_REGION = os.environ.get(AWS_DEFAULT_REGION)
    log_group = "{}_logs".format(queue_name)

    definition = str(task_definition).format(queue_name=queue_name, container_name=container_name, image=image,
                                        AWS_DEFAULT_REGION=AWS_DEFAULT_REGION, challenge_pk=challenge_pk,log_group=log_group)
    definition = eval(definition)

    response = client.register_task_definition(**definition)
    task_def_arn = response["taskDefinition"].get("taskDefinitionArn")
    challenge.task_def_arn = task_def_arn
    challenge.save(['task_def_arn'])

def create_service_by_challenge_pk(challenge, client_token):
    ecs = get_boto3_client("ecs", aws_keys)

    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    task_def_arn = register_task_def_by_challenge_pk(ecs, queue_name, challenge.pk)

    definition = str(service_definition).format(service_name=service_name, task_def_arn=task_def_arn, client_token=client_token)
    definition = eval(definition)

    ecs.create_service(**definition)
    
    Challenge.objects.filter(pk=challenge.pk).update(workers=1)

def update_service_by_challenge_pk(challenge, num_of_tasks):  
    queue_name = challenge.queue
    ecs = get_boto3_client("ecs", aws_keys)
    container_name = "worker_{}".format(queue_name)
    service_name = "{}_service".format(queue_name)
    task_def_arn = challenge.task_def_arn

    try:
        response = ecs.update_service(
        cluster='Challenge_Cluster',
        service='{service_name}',
        desiredCount=num_of_tasks,
        taskDefinition='{task_def_arn}',
        forceNewDeployment=False,  
        ).format(service_name=service_name, task_def_arn=task_def_arn)

        if (response["service"]["serviceName"]==service_name):
            message = {"success":"Service updated succesfully.", "Error":None}
            return message

    except ClientError as e:
        return e.response['Error']['Code']  # Incorporate message display in admin page.

    Challenge.objects.filter(pk=challenge.pk).update(workers=num_of_tasks)

def service_manager(challenge, num_of_tasks=None):
    if challenge.workers is not None:
        update_service_by_challenge_pk(challenge, num_of_tasks)
    else:
        client_token = client_token_generator()
        create_service_by_challenge_pk(challenge, client_token)

def start_workers(queryset):
    ecs = get_boto3_client("ecs", aws_keys)
    for challenge in queryset:
        if(challenge.workers==0):
            response = service_manager(challenge=challenge, num_of_tasks=1)

def stop_workers(queryset):
    ecs = get_boto3_client("ecs", aws_keys)
    for challenge in queryset:
        if(challenge.workers>0):
            service_manager(challenge=challenge, num_of_tasks=0)