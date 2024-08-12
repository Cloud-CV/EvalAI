import os
import pytz
from evalai_interface import EvalAI_Interface
from datetime import datetime, timedelta
from django.conf import settings
import pandas as pd  # new import

utc = pytz.UTC
auth_token = os.environ.get(
    "AUTH_TOKEN",
)
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}

DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE")
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
    "CLUSTER": os.environ.get("CLUSTER", "evalai-prod-cluster"),
}


def get_boto3_client(resource, aws_keys):
    import boto3

    """
    Returns the boto3 client for a resource in AWS
    Arguments:
        resource {str} -- Name of the resource for which client is to be created
        aws_keys {dict} -- AWS keys which are to be used
    Returns:
        Boto3 client object for the resource
    """
    try:
        client = boto3.client(
            resource,
            region_name=aws_keys["AWS_REGION"],
            aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
        )
        return client
    except Exception as e:
        print("Error in creating boto3 client: ", str(e))
        return None


def get_cpu_metrics_for_challenge(
    challenge,
    cluster_name=COMMON_SETTINGS_DICT["CLUSTER"],
    range_days=1,
    period_seconds=300,
):
    """
    Get the CPU Utilization of the worker in the challenge.
    """

    cloudwatch_client = get_boto3_client("cloudwatch", aws_keys)

    start_time = datetime.utcnow() - timedelta(days=range_days)
    end_time = datetime.utcnow()
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)

    response = cloudwatch_client.get_metric_statistics(
        Namespace="AWS/ECS",
        MetricName="CPUUtilization",
        Dimensions=[
            {"Name": "ClusterName", "Value": cluster_name},
            {"Name": "ServiceName", "Value": service_name},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=period_seconds,
        Statistics=["Average", "Maximum", "Minimum"],
    )

    return response["Datapoints"]


def get_memory_metrics_for_challenge(
    challenge,
    cluster_name=COMMON_SETTINGS_DICT["CLUSTER"],
    range_days=1,
    period_seconds=300,
):
    """
    Get the Memory Utilization of the worker in the challenge.
    """

    cloudwatch_client = get_boto3_client("cloudwatch", aws_keys)

    start_time = datetime.utcnow() - timedelta(days=range_days)
    end_time = datetime.utcnow()
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    response = cloudwatch_client.get_metric_statistics(
        Namespace="AWS/ECS",
        MetricName="MemoryUtilization",
        Dimensions=[
            {"Name": "ClusterName", "Value": cluster_name},
            {"Name": "ServiceName", "Value": service_name},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=period_seconds,
        Statistics=["Average", "Maximum", "Minimum"],
    )

    return response["Datapoints"]


def get_storage_metrics_for_challenge(
    challenge,
    cluster_name=COMMON_SETTINGS_DICT["CLUSTER"],
    range_days=1,
    period_seconds=300,
):
    """
    Get the Storage Utilization of the worker in the challenge.
    """

    from datetime import datetime, timedelta

    cloudwatch_client = get_boto3_client("cloudwatch", aws_keys)

    start_time = datetime.utcnow() - timedelta(days=range_days)
    end_time = datetime.utcnow()
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)

    response = cloudwatch_client.get_metric_statistics(
        Namespace="ECS/ContainerInsights",
        MetricName="EphemeralStorageUtilized",
        Dimensions=[
            {"Name": "ClusterName", "Value": cluster_name},
            {"Name": "ServiceName", "Value": service_name},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=period_seconds,
        Statistics=["Average"],
    )

    return response["Datapoints"]


# get current CPU and Memory utilization for a challenge
def current_worker_limit(task_definition_name, metrics):
    ecs_client = get_boto3_client("ecs", aws_keys)
    try:
        response = ecs_client.describe_task_definition(
            taskDefinition=task_definition_name
        )
    except Exception as e:
        print(f"Error retrieving task definition: {str(e)}")
        return {}

    task_definition = response.get("taskDefinition", {})
    return task_definition.get(metrics, 0)


def get_new_resource_limit(
    metrics, metric_name, service_name, current_metric_limit
):
    """Categorize CPU or Memory metrics and decide on scaling actions separately."""

    # Calculate average of the provided metrics
    average = sum(
        datapoint["Average"] for datapoint in metrics if "Average" in datapoint
    ) / len(metrics)

    # Apply separate logic based on whether the metric is CPU or Memory
    if metric_name == "CPU":
        # CPU-specific scaling logic
        if average <= 25:
            # if average smaller than 25%, scale down
            print(
                f"Scaling down {service_name} due to low {metric_name} utilization"
            )
            new_limit = str(int(current_metric_limit) // 2)
        elif average >= 75:
            # if average greater than 75%, scale up
            print(
                f"Scaling up {service_name} due to high {metric_name} utilization"
            )
            new_limit = str(int(current_metric_limit) * 2)
        else:
            # no scaling action required
            print(
                f"No scaling action required for {service_name} based on {metric_name} utilization"
            )
            new_limit = current_metric_limit
        return new_limit
    elif metric_name == "Memory":
        if average <= 25:
            # if average smaller than 25%, scale down
            print(
                f"Scaling down {service_name} due to low {metric_name} utilization"
            )
            new_limit = str(int(current_metric_limit) // 2)
        elif average >= 75:
            # if average greater than 75%, scale up
            print(
                f"Scaling up {service_name} due to high {metric_name} utilization"
            )
            new_limit = str(int(current_metric_limit) * 2)
        else:
            # no scaling action required
            print(
                f"No scaling action required for {service_name} based on {metric_name} utilization"
            )
            new_limit = current_metric_limit
        return new_limit


def get_task_definition_details(task_definition_name):
    ecs_client = get_boto3_client("ecs", aws_keys)
    try:
        response = ecs_client.describe_task_definition(
            taskDefinition=task_definition_name
        )
    except Exception as e:
        print(f"Error retrieving task definition: {str(e)}")
        return {}

    task_definition = response.get("taskDefinition", {})

    details = {
        "family": task_definition.get("family", ""),
        "executionRoleArn": task_definition.get("executionRoleArn", ""),
        "networkMode": task_definition.get("networkMode", ""),
        "cpu": task_definition.get("cpu", ""),
        "memory": task_definition.get("memory", ""),
        "ephemeralStorage": task_definition.get(
            "ephemeralStorage", {"sizeInGiB": 21}
        ),
        "requiresCompatibilities": task_definition.get(
            "requiresCompatibilities", []
        ),
        "containers": [],
        "revision": task_definition.get("revision", 0),
    }

    # Correctly format the environment dictionary into a list of dictionaries
    container_info = {
        "name": task_definition["containerDefinitions"][0].get("name", ""),
        "image": task_definition["containerDefinitions"][0].get("image", ""),
        "cpu": task_definition["containerDefinitions"][0].get("cpu", 0),
        "essential": task_definition["containerDefinitions"][0].get(
            "essential", False
        ),
        "environment": task_definition["containerDefinitions"][0].get(
            "environment", []
        ),
        "logConfiguration": task_definition["containerDefinitions"][0].get(
            "logConfiguration", {}
        ),
        "workingDirectory": task_definition["containerDefinitions"][0].get(
            "workingDirectory", "/code"
        ),
    }
    details["containers"].append(container_info)

    return details


def readjust_worker_limit(
    task_definition_name, new_cpu_limit, new_memory_limit
):
    ecs_client = get_boto3_client("ecs", aws_keys)
    """Update the ECS task definition with new CPU and memory settings while retaining all other configuration details.

    Args:
        family (str): The family name of the task definition to update.
        new_cpu (str): The new CPU value to set for the task (in CPU units, e.g., '256' for 0.25 vCPU).
        new_memory (str): The new memory value to set for the task (in MiB, e.g., '512' for 512 MiB).

    Returns:
        dict: The response from the ECS API containing the updated task definition details.
    """

    # Get all details of the current task definition
    details = get_task_definition_details(
        task_definition_name=task_definition_name
    )

    # Register the new task definition with updated settings
    response = ecs_client.register_task_definition(
        family=details["family"],
        executionRoleArn=details["executionRoleArn"],
        networkMode=details["networkMode"],
        containerDefinitions=details["containers"],
        volumes=details.get("volumes", []),
        requiresCompatibilities=details["requiresCompatibilities"],
        cpu=new_cpu_limit,  # Update CPU at the task level if applicable
        memory=new_memory_limit,  # Update memory at the task level if applicable
        ephemeralStorage=details["ephemeralStorage"],
    )
    return response


def update_service_to_latest_task_definition(
    cluster_name, service_name, task_family
):
    ecs_client = get_boto3_client("ecs", aws_keys)

    # Get the latest revision of the task definition
    response = ecs_client.describe_task_definition(taskDefinition=task_family)
    task_definition_arn = response["taskDefinition"]["taskDefinitionArn"]
    print("Task Definition ARN:", task_definition_arn)
    # Update the service to use the latest task definition revision
    update_response = ecs_client.update_service(
        cluster=cluster_name,
        service=service_name,
        taskDefinition=task_definition_arn,
    )

    return update_response


def monitor_workers_for_challenge(response, evalai_interface):
    for challenge in response["results"]:
        try:
            cpu_utilization_datapoints = get_cpu_metrics_for_challenge(
                challenge=challenge, range_days=14, period_seconds=3600
            )
            current_cpu_limit = current_worker_limit(challenge.queue, "cpu")
            new_cpu_limit = get_new_resource_limit(
                cpu_utilization_datapoints,
                "CPU",
                f"{challenge['queue']}",
                current_cpu_limit,
            )
        except Exception as e:
            print(
                "Error in getting worker metrics for challenge: ",
                challenge["pk"],
            )
            print("Error: ", str(e))

        try:
            memory_utilization_datapoints = get_memory_metrics_for_challenge(
                challenge
            )
            current_memory_limit = current_worker_limit(
                challenge.queue, "memory"
            )
            new_memory_limit = get_new_resource_limit(
                memory_utilization_datapoints,
                "Memory",
                f"{challenge['queue']}",
                current_memory_limit,
            )
        except Exception as e:
            print(
                "Error in getting worker metrics for challenge: ",
                challenge["pk"],
            )
            print("Error: ", str(e))

        try:
            storage_utilization_datapoints = get_storage_metrics_for_challenge(
                challenge
            )
            print(
                "Storage Utilization Datapoints: ",
                storage_utilization_datapoints,
            )
        except Exception as e:
            print(
                "Error in getting worker metrics for challenge: ",
                challenge["pk"],
            )
            print("Error: ", str(e))

        # readjust the worker limits
        try:
            response = readjust_worker_limit(
                task_definition_name=challenge.queue,
                new_cpu_limit=new_cpu_limit,
                new_memory_limit=new_memory_limit,
            )
            print(
                f"Updated worker limits for {challenge['queue']}: {response}"
            )
        except Exception as e:
            print(
                f"Error in updating worker limits for challenge: {challenge['pk']}"
            )
            print(f"Error: {str(e)}")

        # Update the worker to use the new task definition (latest revision)
        try:
            update_response = update_service_to_latest_task_definition(
                cluster_name=COMMON_SETTINGS_DICT["CLUSTER"],
                service_name=f"{challenge['queue']}_service",
                task_family=challenge.queue,
            )
            print(
                f"Updated service to use latest task definition: {update_response}"
            )
        except Exception as e:
            print(
                f"Error in updating service to use latest task definition for challenge: {challenge['pk']}"
            )
            print(f"Error: {str(e)}")


def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface


# Cron Job
def start_job():
    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()
    monitor_workers_for_challenge(response, evalai_interface)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        monitor_workers_for_challenge(response, evalai_interface)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker metric monitoring script")
    start_job()
    print("Quitting worker metric monitoring script!")
