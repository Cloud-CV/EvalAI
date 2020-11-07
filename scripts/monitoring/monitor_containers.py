import docker
import json
import os
import requests


CHANNEL = "#evalai-deployment-notifications"
DOCKER_CLIENT = docker.DockerClient(base_url="unix://var/run/docker.sock")
EVALAI_CONTAINER_PREFIX = "evalai"
RUNNING = "running"
SLACK_WEBHOOK = os.environ.get("MONITORING_SLACK_WEBHOOK_URL")
USERNAME = "Monitor Bot"
ICON_EMOJI = ":robot_face:"
ENV = os.environ.get("ENV")


def is_container_running(container):
    """
    Verify the status of a container by it's name

    Arguments:
        container {Object} -- Docker container
    Returns:
        is_running {boolean} -- True if container is running
    """
    is_running = False
    try:
        container_state = container.attrs['State']
        is_running = container_state['Status'] == RUNNING
    except Exception:
        pass
    return is_running


def get_container_status():
    """
    Get running container status

    Returns:
        container_status_map {Dict} -- Dict of container status
    """
    container_status_map = {}
    containers = DOCKER_CLIENT.containers.list(all=True)
    for container in containers:
        if EVALAI_CONTAINER_PREFIX in container.name:
            container_status_map[container.name] = is_container_running(container)
    return container_status_map


def notify(container_names):
    """
    Send slack notification for workers which are failing

    Arguments:
        container_names {List} -- List of container names
    """
    environment = "Staging"
    if ENV == "PRODUCTION":
        environment = "Production"
    message = "{} environment:\n\n Following workers are down:\n\n {}".format(environment, " \n ".join(container_names))
    response = requests.post(SLACK_WEBHOOK, data=json.dumps({
        "text": message,
        "username": USERNAME,
        "channel": CHANNEL,
        "icon_emoji": ICON_EMOJI
    }))
    return response


def check_container_status():
    """
    Check container status and send slack notification
    """
    # Containers to check status for
    container_status_map = get_container_status()

    failed_containers = []
    for container, is_running in container_status_map.items():
        if not is_running:
            failed_containers.append(container)

    if len(failed_containers) > 0:
        notify(failed_containers)


if __name__ == "__main__":
    check_container_status()
