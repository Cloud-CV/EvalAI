import os
import pytz
import requests
from evalai_interface import EvalAI_Interface
from datetime import datetime, timedelta

from django.conf import settings

utc = pytz.UTC
auth_token = os.environ.get(
    "AUTH_TOKEN",
)
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}

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
    "STATSD_ENDPOINT": os.environ.get("STATSD_ENDPOINT"),
    "STATSD_PORT": os.environ.get("STATSD_PORT"),
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


def get_cpu_metrics_for_challenge(challenge, cluster_name=COMMON_SETTINGS_DICT["CLUSTER"], range_days=1, period_seconds=300):
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


def get_memory_metrics_for_challenge(challenge, cluster_name=COMMON_SETTINGS_DICT["CLUSTER"], range_days=1, period_seconds=300):
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


def get_storage_metrics_for_challenge(challenge, cluster_name=COMMON_SETTINGS_DICT["CLUSTER"], range_days=1, period_seconds=300):
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


def monitor_workers_for_challenge(response, evalai_interface):
    for challenge in response['results']:
        try:
            cpu_utilization_datapoints = get_cpu_metrics_for_challenge(challenge)
            print("CPU Utilization Datapoints: ", cpu_utilization_datapoints)
        except Exception as e:
            print("Error in getting worker metrics for challenge: ", challenge['pk'])
            print("Error: ", str(e))

        try:
            memory_utilization_datapoints = get_memory_metrics_for_challenge(challenge)
            print("Memory Utilization Datapoints: ", memory_utilization_datapoints)
        except Exception as e:
            print("Error in getting worker metrics for challenge: ", challenge['pk'])
            print("Error: ", str(e))

        try:
            storage_utilization_datapoints = get_storage_metrics_for_challenge(challenge)
            print("Storage Utilization Datapoints: ", storage_utilization_datapoints)
        except Exception as e:
            print("Error in getting worker metrics for challenge: ", challenge['pk'])
            print("Error: ", str(e))


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
