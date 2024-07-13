import datetime
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


def fetch_metrics_in_chunks(endpoint, range_days=1, period_seconds=300):
    max_days_per_request = 1  # Define maximum days per request to 1 day
    metrics_data = []

    start_date = datetime.datetime.now(pytz.UTC) - datetime.timedelta(
        days=range_days
    )
    end_date = datetime.datetime.now(pytz.UTC)

    while start_date < end_date:
        chunk_end_date = min(
            start_date + datetime.timedelta(days=max_days_per_request),
            end_date,
        )
        chunk_range_days = (chunk_end_date - start_date).days
        chunk_endpoint = (
            f"{endpoint}&range={chunk_range_days}&period={period_seconds}"
        )
        response = requests.get(chunk_endpoint, headers=authorization_header)

        if response.status_code == 200:
            metrics_data.append(response.json())
        else:
            print(
                f"Failed to fetch metrics for chunk: {
                    start_date} to {chunk_end_date}"
            )

        start_date = chunk_end_date

    return metrics_data


def get_cpu_metrics_for_challenge(challenge, range_days=1, period_seconds=300):
    get_cpu_metrics_endpoint = f"{evalai_endpoint}/api/challenges/{
        challenge.id}/get_ecs_workers_metrics/cpu/?period={period_seconds}"
    metrics_data = fetch_metrics_in_chunks(
        get_cpu_metrics_endpoint, range_days, period_seconds
    )
    print(
        "CPU Metrics for Challenge ID: {}, Title: {}".format(
            challenge.id, challenge.title
        )
    )
    print(metrics_data)
    return metrics_data


def get_memory_metrics_for_challenge(
    challenge, range_days=1, period_seconds=300
):
    get_memory_metrics_endpoint = f"{evalai_endpoint}/api/challenges/{
        challenge.id}/get_ecs_workers_metrics/memory/?period={period_seconds}"
    metrics_data = fetch_metrics_in_chunks(
        get_memory_metrics_endpoint, range_days, period_seconds
    )
    print(
        "Memory Metrics for Challenge ID: {}, Title: {}".format(
            challenge.id, challenge.title
        )
    )
    print(metrics_data)
    return metrics_data


def get_storage_metrics_for_challenge(
    challenge, range_days=1, period_seconds=300
):
    get_storage_metrics_endpoint = f"{evalai_endpoint}/api/challenges/{
        challenge.id}/get_ecs_workers_metrics/storage/?period={period_seconds}"
    metrics_data = fetch_metrics_in_chunks(
        get_storage_metrics_endpoint, range_days, period_seconds
    )
    print(
        "Storage Metrics for Challenge ID: {}, Title: {}".format(
            challenge.id, challenge.title
        )
    )
    print(metrics_data)
    return metrics_data


def monitor_workers_for_challenge(response, evalai_interface):
    for challenge in response["results"]:
        try:
            cpu_utilization_datapoints = get_cpu_metrics_for_challenge(
                challenge
            )
            memory_utilization_datapoints = get_memory_metrics_for_challenge(
                challenge
            )
            storage_utilization_datapoints = get_storage_metrics_for_challenge(
                challenge
            )

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
