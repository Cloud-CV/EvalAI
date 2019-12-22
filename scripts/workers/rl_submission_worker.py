import logging
import os
import signal
import time

from .worker_util import (
    EvalAI_Interface
)

from kubernetes import client, config


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


logger = logging.getLogger(__name__)

AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "x")
DJANGO_SERVER = os.environ.get("DJANGO_SERVER", "http://localhost")
DJANGO_SERVER_PORT = os.environ.get("DJANGO_SERVER_PORT", "8000")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")
ENVIRONMENT_IMAGE = os.environ.get("ENVIRONMENT_IMAGE", "x:tag")
MESSAGE_FETCH_DEPLAY = int(os.environ.get("MESSAGE_FETCH_DEPLAY", "5"))


def create_deployment_object(image, submission, message):
    PYTHONUNBUFFERED_ENV = client.V1EnvVar(
        name="PYTHONUNBUFFERED",
        value="1",
    )
    AUTH_TOKEN_ENV = client.V1EnvVar(
        name="AUTH_TOKEN",
        value=AUTH_TOKEN
    )
    DJANGO_SERVER_ENV = client.V1EnvVar(
        name="DJANGO_SERVER",
        value=DJANGO_SERVER
    )
    MESSAGE_BODY_ENV = client.V1EnvVar(
        name="BODY",
        value=str(message)
    )
    agent_container = client.V1Container(
        name="agent",
        image=image,
        env=[PYTHONUNBUFFERED_ENV]
    )
    environment_container = client.V1Container(
        name="environment",
        image=ENVIRONMENT_IMAGE,
        env=[PYTHONUNBUFFERED_ENV, AUTH_TOKEN_ENV, DJANGO_SERVER_ENV, MESSAGE_BODY_ENV]
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "evaluation"}),
        spec=client.V1PodSpec(containers=[environment_container, agent_container]))
    spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=1,
        template=template)
    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name="submission-{0}".format(submission)),
        spec=spec)
    return deployment


def create_deployment(api_instance, deployment):
    api_response = api_instance.create_namespaced_deployment(
        body=deployment,
        namespace="default")
    logger.info("Deployment created. status='%s'" % str(api_response.status))


def process_submission_callback(message, api):
    config.load_kube_config()
    extensions_v1beta1 = client.ExtensionsV1beta1Api()
    logger.info(message)
    submission_data = {
        "submission_status": "running",
        "submission": message["submission_pk"],
    }
    logger.info(submission_data)
    api.update_submission_status(submission_data, message["challenge_pk"])
    dep = create_deployment_object(
        message["submitted_image_uri"],
        message["submission_pk"],
        message
    )
    create_deployment(extensions_v1beta1, dep)


def main():
    api = EvalAI_Interface(
        AUTH_TOKEN=AUTH_TOKEN,
        DJANGO_SERVER=DJANGO_SERVER,
        DJANGO_SERVER_PORT=DJANGO_SERVER_PORT,
        QUEUE_NAME=QUEUE_NAME,
    )
    logger.info("String RL Worker for {}".format(api.get_challenge_by_queue_name()["title"]))
    killer = GracefulKiller()
    while True:
        logger.info(
            "Fetching new messages from the queue {}".format(QUEUE_NAME)
        )
        message = api.get_message_from_sqs_queue()
        logger.info(message)
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            submission = api.get_submission_by_pk(submission_pk)
            if submission:
                if submission.get("status") == "finished":
                    message_receipt_handle = message.get("receipt_handle")
                    api.delete_message_from_sqs_queue(message_receipt_handle)
                elif submission.get("status") == "running":
                    continue
                else:
                    message_receipt_handle = message.get("receipt_handle")
                    logger.info(
                        "Processing message body: {}".format(message_body)
                    )
                    process_submission_callback(message_body, api)
                    api.delete_message_from_sqs_queue(message.get("receipt_handle"))
        time.sleep(MESSAGE_FETCH_DEPLAY)
        if killer.kill_now:
            break


if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
