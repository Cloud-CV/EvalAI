import os
import pytz
import requests
from datetime import datetime
from evalai_interface import EvalAI_Interface

utc = pytz.UTC
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}

ENV = os.environ.get("ENV", "dev")


def get_cpu_metrics_for_challenge(challenge):
    get_cpu_metrics_endpoint = "{}/api/challenges/{}/get_ecs_workers_metrics/cpu/".format(
        evalai_endpoint, challenge.id
    )
    response = requests.get(get_cpu_metrics_endpoint, headers=authorization_header)
    print("CPU Metrics for Challenge ID: {}, Title: {}".format(challenge.id, challenge.title))
    print(response.json())


def get_memory_metrics_for_challenge(challenge):
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    get_memory_metrics_endpoint = "{}/api/challenges/{}/get_ecs_workers_metrics/memory/".format(
        evalai_endpoint, challenge.id
    )
    response = requests.get(get_memory_metrics_endpoint, headers=authorization_header)
    print("Memory Metrics for Challenge ID: {}, Title: {}".format(challenge.id, challenge.title))
    print(response.json())


def get_storage_metrics_for_challenge(challenge):
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    get_storage_metrics_endpoint = "{}/api/challenges/{}/get_ecs_workers_metrics/storage/".format(
        evalai_endpoint, challenge.id
    )
    response = requests.get(get_storage_metrics_endpoint, headers=authorization_header)
    print("Storage Metrics for Challenge ID: {}, Title: {}".format(challenge.id, challenge.title))
    print(response.json())


def monitor_workers_for_challenge(response, evalai_interface):
    for challenge in response['results']:
        try:
            # Get the CPU metrics for 1 days
            get_cpu_metrics_for_challenge(challenge)
            # Get the memory metrics for 1 days
            get_memory_metrics_for_challenge(challenge)
            # Get the utilization storage metrics for 1 days
            get_storage_metrics_for_challenge(challenge)
        
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
    scale_up_or_down_workers_for_challenges(response, evalai_interface)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        scale_up_or_down_workers_for_challenges(response, evalai_interface)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker metric monitoring script")
    start_job()
    print("Quitting worker metric monitoring script!")
