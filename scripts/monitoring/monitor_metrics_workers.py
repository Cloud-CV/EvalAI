import os
import pytz
import requests
from evalai_interface import EvalAI_Interface

utc = pytz.UTC
auth_token = os.environ.get(
    "AUTH_TOKEN",
)
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}

ENV = os.environ.get("ENV", "dev")


def get_cpu_metrics_for_challenge(challenge, range_days=1, period_seconds=300):
    get_cpu_metrics_endpoint = "{}/api/challenges/{}/get_ecs_workers_metrics/cpu/?range={}&period={}".format(
        evalai_endpoint, challenge.id, range_days, period_seconds
    )
    response = requests.get(
        get_cpu_metrics_endpoint, headers=authorization_header
    )
    print(
        "CPU Metrics for Challenge ID: {}, Title: {}".format(
            challenge.id, challenge.title
        )
    )
    print(response)


def get_memory_metrics_for_challenge(
    challenge, range_days=1, period_seconds=300
):
    get_memory_metrics_endpoint = "{}/api/challenges/{}/get_ecs_workers_metrics/memory/?range={}&period={}".format(
        evalai_endpoint, challenge.id, range_days, period_seconds
    )
    response = requests.get(
        get_memory_metrics_endpoint, headers=authorization_header
    )
    print(
        "Memory Metrics for Challenge ID: {}, Title: {}".format(
            challenge.id, challenge.title
        )
    )
    print(response)


def get_storage_metrics_for_challenge(
    challenge, range_days=1, period_seconds=300
):
    get_storage_metrics_endpoint = "{}/api/challenges/{}/get_ecs_workers_metrics/storage/?range={}&period={}".format(
        evalai_endpoint, challenge.id, range_days, period_seconds
    )
    response = requests.get(
        get_storage_metrics_endpoint, headers=authorization_header
    )
    print(
        "Storage Metrics for Challenge ID: {}, Title: {}".format(
            challenge.id, challenge.title
        )
    )
    print(response)


def monitor_workers_for_challenge(response, evalai_interface):
    for challenge in response["results"]:
        try:
            cpu_utilization_datapoints = get_cpu_metrics_for_challenge(
                challenge)
            memory_utilization_datapoints = get_memory_metrics_for_challenge(
                challenge)
            storage_utilization_datapoints = get_storage_metrics_for_challenge(
                challenge)

            # log the metrics with print
            print(cpu_utilization_datapoints)
            print(memory_utilization_datapoints)
            print(storage_utilization_datapoints)

        except Exception as e:
            print("Error while fetching metrics for challenge: {}".format(e))
            continue


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
