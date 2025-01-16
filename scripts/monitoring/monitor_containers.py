import docker
import json
import os
import requests
import time

CHANNEL = "#evalai-deployment-notifications"
EVALAI_CONTAINER_PREFIX = "evalai"
RUNNING = "running"
SLACK_WEBHOOK = os.environ.get("MONITORING_SLACK_WEBHOOK_URL")
USERNAME = "Monitor Bot"
ICON_EMOJI = ":robot_face:"
ENV = os.environ.get("ENV")


def get_environment():
    """
    Get script environment

    Returns:
        environment {str} -- staging/production environment
    """
    environment = "Staging"
    if ENV == "PRODUCTION":
        environment = "Production"
    return environment


def is_container_running(container):
    """
    Verify the status of a container by its name

    Arguments:
        container {Object} -- Docker container
    Returns:
        is_running {boolean} -- True if container is running
    """
    return container.status == RUNNING

def wait_for_submission_file(signal_file_path, submission_file_path):
    """
    Wait for the signal file to indicate that the submission.csv file is ready

    Arguments:
        signal_file_path {str} -- Path to the signal file
        submission_file_path {str} -- Path to the submission.csv file
    """
    while not os.path.exists(signal_file_path):
        print("kubectl logs <pod-name> -c submission-container
Waiting for submission file...")
        time.sleep(5)

    # Process the submission.csv file
    with open(submission_file_path, 'r') as f:
        submission_data = f.read()
        # Process the submission data
        print("Processing submission data...")

# Main function to monitor containers
def main():
    client = docker.from_env()
    containers = client.containers.list(all=True)
    for container in containers:
        if container.name.startswith(EVALAI_CONTAINER_PREFIX):
            if not is_container_running(container):
                message = f"Container {container.name} is not running in {get_environment()} environment."
                print(message)
                if SLACK_WEBHOOK:
                    payload = {
                        "channel": CHANNEL,
                        "username": USERNAME,
                        "text": message,
                        "icon_emoji": ICON_EMOJI,
                    }
                    requests.post(SLACK_WEBHOOK, data=json.dumps(payload))

    # Wait for the submission file
    wait_for_submission_file('submission_ready.txt', 'submission.csv')

if __name__ == "__main__":
    # Example usage of find_file_path
    signal_file_path = find_file_path('submission_ready.txt')
    submission_file_path = find_file_path('submission.csv')
    if signal_file_path and submission_file_path:
        wait_for_submission_file(signal_file_path, submission_file_path)
    else:
        print("Required files not found.")
    main()