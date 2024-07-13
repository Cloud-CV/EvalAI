import datetime
import os
import pytz
import requests
from evalai_interface import EvalAI_Interface

# Constants
utc = pytz.UTC
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
EVALAI_ENDPOINT = os.getenv("API_HOST_URL")
AUTH_HEADER = {"Authorization": f"Bearer {AUTH_TOKEN}"}
ENV = os.getenv("ENV", "dev")

def fetch_metrics_in_chunks(endpoint, range_days=1, period_seconds=300):
    max_days_per_request = 1  # Max days per request
    metrics_data = []
    start_date = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=range_days)
    end_date = datetime.datetime.now(pytz.UTC)

    while start_date < end_date:
        chunk_end_date = min(start_date + datetime.timedelta(days=max_days_per_request), end_date)
        chunk_range_days = (chunk_end_date - start_date).days
        chunk_endpoint = f"{endpoint}&range={chunk_range_days}&period={period_seconds}"
        response = requests.get(chunk_endpoint, headers=AUTH_HEADER)

        if response.status_code == 200:
            metrics_data.append(response.json())
        else:
            print(f"Failed to fetch metrics for chunk: {start_date} to {chunk_end_date}")

        start_date = chunk_end_date
    return metrics_data

def get_metrics_for_challenge(challenge, metric_type, range_days=1, period_seconds=300):
    endpoint = f"{EVALAI_ENDPOINT}/api/challenges/{challenge.id}/get_ecs_workers_metrics/{metric_type}/?period={period_seconds}"
    metrics_data = fetch_metrics_in_chunks(endpoint, range_days, period_seconds)
    print(f"{metric_type.capitalize()} Metrics for Challenge ID: {challenge.id}, Title: {challenge.title}")
    print(metrics_data)
    return metrics_data

def monitor_workers_for_challenge(response, evalai_interface):
    for challenge in response["results"]:
        try:
            cpu_utilization_datapoints = get_metrics_for_challenge(challenge, 'cpu')
            memory_utilization_datapoints = get_metrics_for_challenge(challenge, 'memory')
            storage_utilization_datapoints = get_metrics_for_challenge(challenge, 'storage')

            # Log the metrics
            print(cpu_utilization_datapoints)
            print(memory_utilization_datapoints)
            print(storage_utilization_datapoints)

        except Exception as e:
            print(f"Error while fetching metrics for challenge: {e}")
            continue

def create_evalai_interface():
    evalai_interface = EvalAI_Interface(AUTH_TOKEN, EVALAI_ENDPOINT)
    return evalai_interface

def start_job():
    evalai_interface = create_evalai_interface()
    response = evalai_interface.get_challenges()
    monitor_workers_for_challenge(response, evalai_interface)
    next_page = response["next"]
    while next_page:
        response = evalai_interface.make_request(next_page, "GET")
        monitor_workers_for_challenge(response, evalai_interface)
        next_page = response["next"]

if __name__ == "__main__":
    print("Starting worker metric monitoring script")
    start_job()
    print("Quitting worker metric monitoring script!")
