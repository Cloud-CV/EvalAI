import argparse
import json
import os
from datetime import datetime, timedelta

import numpy as np
import pytz
from auto_stop_workers import delete_worker
from evalai_interface import EvalAI_Interface

utc = pytz.UTC

evalai_endpoint = os.environ.get("API_HOST_URL")
auth_token = os.environ.get("AUTH_TOKEN")
json_path = os.environ.get("JSON_PATH", "~/evalai_aws_keys.json")

with open(json_path) as f:
    aws_keys = json.load(f)


def get_boto3_client(resource, aws_keys):
    import boto3

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


def get_aws_metrics_for_challenge(
    challenge, args, aws_namespace, aws_metric_name
):
    cloudwatch_client = get_boto3_client("cloudwatch", aws_keys)

    start_time = datetime.utcnow() - timedelta(days=args.range_days)
    end_time = datetime.utcnow()
    queue_name = challenge["queue"]
    service_name = "{}_service".format(queue_name)

    response = cloudwatch_client.get_metric_statistics(
        Namespace=aws_namespace,
        MetricName=aws_metric_name,
        Dimensions=[
            {"Name": "ClusterName", "Value": args.cluster_name},
            {"Name": "ServiceName", "Value": service_name},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=args.period_seconds,
        Statistics=["Average"],
    )

    return response["Datapoints"]


def get_metrics_for_challenge(metric, challenge, args):
    if metric == "cpu":
        aws_namespace = "AWS/ECS"
        aws_metric_name = "CPUUtilization"
    elif metric == "memory":
        aws_namespace = "AWS/ECS"
        aws_metric_name = "MemoryUtilization"
    elif metric == "storage":
        aws_namespace = "ECS/ContainerInsights"
        aws_metric_name = "EphemeralStorageUtilized"
    else:
        raise NotImplementedError(f"Metric {metric} not implemented")

    return get_aws_metrics_for_challenge(
        challenge, args, aws_namespace, aws_metric_name
    )


def get_new_resource_limit(
    metrics, metric_name, challenge, current_metric_limit
):
    max_average_consumption = np.max(
        list(
            datapoint["Average"]
            for datapoint in metrics
            if "Average" in datapoint
        )
    )

    if metric_name == "memory":
        min_limit = 256
        max_limit = 16384
    elif metric_name == "cpu":
        min_limit = 128
        max_limit = 4096
    else:  # storage
        min_limit = 21
        max_limit = 50
    if max_average_consumption <= 25:
        new_limit = max(current_metric_limit // 2, min_limit)
    elif max_average_consumption >= 75:
        new_limit = min(int(current_metric_limit) * 2, max_limit)
    else:
        new_limit = current_metric_limit
    return new_limit


def allocate_resources_for_challenge(challenge, evalai_interface, args):
    old_limits = {}
    new_limits = {}
    for metric, attribute_name in [
        ("cpu", "worker_cpu_cores"),
        ("memory", "worker_memory"),
    ]:
        try:
            datapoints = get_metrics_for_challenge(metric, challenge, args)
            if datapoints == []:
                # challenge hasn't been run
                print("No data points found!")
                return

            current_limit = challenge[attribute_name]
            new_limit = get_new_resource_limit(
                datapoints,
                metric,
                challenge,
                current_limit,
            )
            old_limits[metric] = current_limit
            new_limits[metric] = new_limit
        except Exception as e:
            print(
                f"Error in getting {metric} metrics for challenge: ",
                challenge["id"],
            )
            print("Error: ", str(e))
            return

    # if new limit is not same as old limit for any metric: delete the worker, update backend
    # start stop is handled by the auto scale scriptt
    if (
        old_limits["cpu"] != new_limits["cpu"]
        or old_limits["memory"] != new_limits["memory"]
    ):
        print("Old Limits: ", old_limits)
        print("New Limits: ", new_limits)
        delete_worker(challenge["id"])
        try:
            data = {
                "challenge_pk": challenge["id"],
                "worker_cpu_cores": new_limits["cpu"],
                "worker_memory": new_limits["memory"],
            }
            payload = json.dumps(data)
            response = evalai_interface.update_challenge_attributes(payload)
            print(f"Updated backend for challenge: {challenge['id']}")
        except Exception as e:
            print(
                f"Error in updating backend for challenge: {challenge['id']}"
            )
            print(f"Error: {str(e)}")

    else:
        print(f"No changes required for challenge: {challenge['id']}")


def allocate_resources_for_challenges(response, evalai_interface, args):
    for challenge in response["results"]:
        print(
            "For challenge: ", challenge["id"], " queue: ", challenge["queue"]
        )
        allocate_resources_for_challenge(challenge, evalai_interface, args)
        print("=" * 30)


def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface


# Cron Job
def start_job():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cluster-name",
        help="Name of the ECS cluster",
        type=str,
        default="evalai-prod-cluster",
    )
    parser.add_argument(
        "--range-days",
        help="Number of days to consider for metrics",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--period-seconds",
        help="Period in seconds for metrics",
        type=int,
        default=3600,  # Default is 1 hour
    )
    args = parser.parse_args()

    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()
    allocate_resources_for_challenges(response, evalai_interface, args)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        allocate_resources_for_challenges(response, evalai_interface, args)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting auto allocate ecs resources script")
    start_job()
    print("Quitting auto allocate ecs resources script!")
