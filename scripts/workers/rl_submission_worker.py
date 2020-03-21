import logging
import os
import signal

from worker_utils import EvalAI_Interface

from kubernetes import client, config

# TODO: Add exception in all the commands
# from kubernetes.client.rest import ApiException


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


logger = logging.getLogger(__name__)
config.load_kube_config()
batch_v1 = client.BatchV1Api()

AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "auth_token")
EVALAI_API_SERVER = os.environ.get(
    "EVALAI_API_SERVER", "http://localhost:8000"
)
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")


def create_job_object(message, environment_image):
    """Function to create the AWS EKS Job object

    Arguments:
        message {[dict]} -- Submission message from AWS SQS queue

    Returns:
        [AWS EKS Job class object] -- AWS EKS Job class object
    """

    PYTHONUNBUFFERED_ENV = client.V1EnvVar(name="PYTHONUNBUFFERED", value="1")
    AUTH_TOKEN_ENV = client.V1EnvVar(name="AUTH_TOKEN", value=AUTH_TOKEN)
    EVALAI_API_SERVER_ENV = client.V1EnvVar(
        name="EVALAI_API_SERVER", value=EVALAI_API_SERVER
    )
    MESSAGE_BODY_ENV = client.V1EnvVar(name="BODY", value=str(message))
    submission_pk = message["submission_pk"]
    image = message["submitted_image_uri"]
    # Configureate Pod agent container
    agent_container = client.V1Container(
        name="agent", image=image, env=[PYTHONUNBUFFERED_ENV]
    )
    # Configureate Pod environment container
    environment_container = client.V1Container(
        name="environment",
        image=environment_image,
        env=[
            PYTHONUNBUFFERED_ENV,
            AUTH_TOKEN_ENV,
            EVALAI_API_SERVER_ENV,
            MESSAGE_BODY_ENV,
        ],
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "evaluation"}),
        spec=client.V1PodSpec(
            containers=[environment_container, agent_container],
            restart_policy="Never",
        ),
    )
    # Create the specification of deployment
    spec = client.V1JobSpec(backoff_limit=1, template=template)
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name="submission-{0}".format(submission_pk)
        ),
        spec=spec,
    )
    return job


def create_job(api_instance, job):
    """Function to create a job on AWS EKS cluster

    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating job
        job {[AWS EKS job object]} -- Job object returned after running create_job_object fucntion

    Returns:
        [V1Job object] -- [AWS EKS V1Job]
        For reference: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Job.md
    """
    api_response = api_instance.create_namespaced_job(
        body=job, namespace="default", pretty=True
    )
    logger.info("Deployment created. status='%s'" % str(api_response.status))
    return api_response


def delete_job(api_instance, job_name):
    """Function to delete a job on AWS EKS cluster

    Arguments:
        api_instance {[AWS EKS API object]} -- API object for deleting job
        job_name {[string]} -- Name of the job to be terminated
    """
    api_response = api_instance.delete_namespaced_job(
        name=job_name,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    logger.info("Job deleted. status='%s'" % str(api_response.status))


def process_submission_callback(body, challenge_phase, evalai):
    """Function to process submission message from SQS Queue

    Arguments:
        body {[dict]} -- Submission message body from AWS SQS Queue
        evalai {[EvalAI class object]} -- EvalAI class object imported from worker_utils
    """
    try:
        logger.info("[x] Received submission message %s" % body)
        environment_image = challenge_phase.get("environment_image")
        job = create_job_object(body, environment_image)
        response = create_job(batch_v1, job)
        submission_data = {
            "submission_status": "running",
            "submission": body["submission_pk"],
            "job_name": response.metadata.name,
        }
        evalai.update_submission_status(submission_data, body["challenge_pk"])
    except Exception as e:
        logger.exception(
            "Exception while receiving message from submission queue with error {}".format(
                e
            )
        )


def main():
    killer = GracefulKiller()
    evalai = EvalAI_Interface(
        AUTH_TOKEN=AUTH_TOKEN,
        EVALAI_API_SERVER=EVALAI_API_SERVER,
        QUEUE_NAME=QUEUE_NAME,
    )
    logger.info(
        "Deploying Worker for {}".format(
            evalai.get_challenge_by_queue_name()["title"]
        )
    )
    while True:
        logger.info(
            "Fetching new messages from the queue {}".format(QUEUE_NAME)
        )
        message = evalai.get_message_from_sqs_queue()
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            challenge_pk = message_body.get("challenge_pk")
            phase_pk = message_body.get("phase_pk")
            submission = evalai.get_submission_by_pk(submission_pk)
            if submission:
                if (
                    submission.get("status") == "finished"
                    or submission.get("status") == "failed"
                    or submission.get("status") == "cancelled"
                ):
                    # Fetch the last job name from the list as it is the latest running job
                    job_name = submission.get("job_name")[-1]
                    delete_job(batch_v1, job_name)
                    message_receipt_handle = message.get("receipt_handle")
                    evalai.delete_message_from_sqs_queue(
                        message_receipt_handle
                    )
                elif submission.get("status") == "running":
                    continue
                else:
                    message_receipt_handle = message.get("receipt_handle")
                    logger.info(
                        "Processing message body: {0}".format(message_body)
                    )
                    challenge_phase = evalai.get_challenge_phase_by_pk(
                        challenge_pk, phase_pk
                    )
                    process_submission_callback(
                        message_body, challenge_phase, evalai
                    )
        if killer.kill_now:
            break


if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
