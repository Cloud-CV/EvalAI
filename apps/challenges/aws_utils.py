import logging
import os
import random
import string
import yaml

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from http import HTTPStatus

from base.utils import get_boto3_client
from evalai.celery import app

logger = logging.getLogger(__name__)

DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
ENV = DJANGO_SETTINGS_MODULE.split(".")[-1]
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
    "AWS_DEFAULT_REGION": aws_keys["AWS_REGION"],
    "AWS_ACCOUNT_ID": aws_keys["AWS_ACCOUNT_ID"],
    "AWS_ACCESS_KEY_ID": aws_keys["AWS_ACCESS_KEY_ID"],
    "AWS_SECRET_ACCESS_KEY": aws_keys["AWS_SECRET_ACCESS_KEY"],
    "AWS_STORAGE_BUCKET_NAME": aws_keys["AWS_STORAGE_BUCKET_NAME"],
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
    "CPU": os.environ.get("CPU", 1024),
    "MEMORY": os.environ.get("MEMORY", 2048),
    "CLUSTER": os.environ.get("CLUSTER", "evalai-prod-cluster"),
    "DJANGO_SERVER": os.environ.get("DJANGO_SERVER", "localhost"),
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
    "SUBNET_1": os.environ.get("SUBNET_1", "subnet-e260d5be"),
    "SUBNET_2": os.environ.get("SUBNET_2", "subnet-300ea557"),
    "SUBNET_SECURITY_GROUP": os.environ.get(
        "SUBNET_SECURITY_GROUP", "sg-148b4a5e"
    ),
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
                  "value": "{AWS_DEFAULT_REGION}"
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
            ],
            "workingDirectory": "/code",
            "readonlyRootFilesystem": False,
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "evalai-worker-{ENV}",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "{queue_name}",
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


def client_token_generator():
    """
    Returns a 32 characters long client token to ensure idempotency with create_service boto3 requests.

    Parameters: None

    Returns:
    str: string of size 32 composed of digits and letters
    """

    client_token = "".join(
        random.choices(string.ascii_letters + string.digits, k=32)
    )
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
    execution_role_arn = COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"]

    if execution_role_arn:
        definition = task_definition.format(
            queue_name=queue_name,
            container_name=container_name,
            ENV=ENV,
            challenge_pk=challenge.pk,
            **COMMON_SETTINGS_DICT
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
            **VPC_DICT
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
        client_token = client_token_generator()
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
        else:
            response = "Please select challenges with active workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}


def restart_workers(queryset):
    """
    The function called by the admin action method to restart all the selected workers.

    Calls the delete_service_by_challenge_pk method. Before calling, verifies that the challenge worker(s) is(are) active.

    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.

    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(
                client,
                challenge,
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
    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))
    if prev != curr:
        if field_name == "test_annotation":
            challenge = instance.challenge
        else:
            challenge = instance
        restart_workers([challenge])
        logger.info(
            "The worker service for challenge {} was restarted, as {} was changed.".format(
                instance.pk, field_name
            )
        )


@app.task
def create_eks_nodegroup(challenge, cluster_name):
    """
    Creates a nodegroup when a EKS cluster is created by the EvalAI admin
    Arguments:
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
        cluster_name {str} -- name of eks cluster
    """
    nodegroup_name = "{0}-nodegroup".format(challenge.title.replace(" ", "-"))
    client = get_boto3_client("eks", aws_keys)
    # TODO: Move the hardcoded cluster configuration such as the
    # instance_type, subnets, AMI to challenge configuration later.
    try:
        response = client.create_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name,
            scalingConfig={"minSize": 1, "maxSize": 10, "desiredSize": 1},
            diskSize=100,
            subnets=[VPC_DICT["SUBNET_1"], VPC_DICT["SUBNET_2"], ],
            instanceTypes=["g4dn.xlarge"],
            amiType="AL2_x86_64_GPU",
            nodeRole=settings.EKS_NODEGROUP_ROLE_ARN,
        )
    except ClientError as e:
        logger.exception(e)
        return response
    waiter = client.get_waiter("nodegroup_active")
    waiter.wait(
        clusterName=cluster_name, nodegroupName=nodegroup_name,
    )


@app.task
def create_eks_cluster(sender, challenge, field_name, **kwargs):
    """
    Called when Challenge is approved by the EvalAI admin
    calls the create_eks_nodegroup function

    Arguments:
        sender {type} -- model field called the post hook
        instance {<class 'django.db.models.query.QuerySet'>} -- instance of the model calling the post hook
    """
    from .models import ChallengeEvaluationCluster

    cluster_name = "{0}-cluster".format(challenge.title.replace(" ", "-"))
    if challenge.approved_by_admin and challenge.is_docker_based:
        client = get_boto3_client("eks", aws_keys)
        try:
            response = client.create_cluster(
                name=cluster_name,
                version="1.15",
                roleArn=settings.EKS_CLUSTER_ROLE_ARN,
                resourcesVpcConfig={
                    "subnetIds": [VPC_DICT["SUBNET_1"], VPC_DICT["SUBNET_2"], ],
                    "securityGroupIds": [VPC_DICT["SUBNET_SECURITY_GROUP"], ],
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
            ChallengeEvaluationCluster.objects.create(
                challenge=challenge,
                name=cluster_name,
                cluster_endpoint=cluster_ep,
                cluster_ssl=cluster_cert,
            )
            # Creating nodegroup
            create_eks_nodegroup(challenge, cluster_name)
            return response
        except ClientError as e:
            logger.exception(e)
            return
