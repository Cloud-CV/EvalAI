import json
import logging
import os
import signal
import urllib.request
import yaml


from worker_utils import EvalAI_Interface

from kubernetes import client

# TODO: Add exception in all the commands
from kubernetes.client.rest import ApiException


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


logger = logging.getLogger(__name__)

AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "auth_token")
EVALAI_API_SERVER = os.environ.get(
    "EVALAI_API_SERVER", "http://localhost:8000"
)
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")


def get_volume_mount_list(mount_path):
    pvc_claim_name = "efs-claim"
    volume_mount = client.V1VolumeMount(
        mount_path=mount_path, name=pvc_claim_name
    )
    logger.info("Volume mount created at path: %s" % str(mount_path))
    volume_mount_list = [volume_mount]
    return volume_mount_list


def get_volume_list():
    pvc_claim_name = "efs-claim"
    persistent_volume_claim = client.V1PersistentVolumeClaimVolumeSource(
        claim_name=pvc_claim_name
    )
    volume = client.V1Volume(
        persistent_volume_claim=persistent_volume_claim, name=pvc_claim_name
    )
    logger.info("Volume object created for '%s' pvc" % str(pvc_claim_name))
    volume_list = [volume]
    return volume_list


def get_submission_meta_update_curl(submission_pk):
    url = "{}/api/jobs/submission/{}/update_started_at/".format(
        EVALAI_API_SERVER, submission_pk
    )
    curl_request = "curl --location --request PATCH '{}' --header 'Authorization: Bearer {}'".format(
        url, AUTH_TOKEN
    )
    return curl_request


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
    MESSAGE_BODY_ENV = client.V1EnvVar(name="BODY", value=json.dumps(message))
    submission_pk = message["submission_pk"]
    image = message["submitted_image_uri"]
    # Configureate Pod agent container
    agent_container = client.V1Container(
        name="agent", image=image, env=[PYTHONUNBUFFERED_ENV]
    )
    volume_mount_list = get_volume_mount_list("/dataset")
    curl_request = get_submission_meta_update_curl(submission_pk)
    # Configure init container
    init_container = client.V1Container(
        name="init-container",
        image="busybox",
        command="/bin/sh",
        args=["-c", curl_request],
    )
    # Configure Pod environment container
    environment_container = client.V1Container(
        name="environment",
        image=environment_image,
        env=[
            PYTHONUNBUFFERED_ENV,
            AUTH_TOKEN_ENV,
            EVALAI_API_SERVER_ENV,
            MESSAGE_BODY_ENV,
        ],
        resources=client.V1ResourceRequirements(
            limits={"nvidia.com/gpu": "1"}
        ),
        volume_mounts=volume_mount_list,
    )
    volume_list = get_volume_list()
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "evaluation"}),
        spec=client.V1PodSpec(
            init_containers=[init_container],
            containers=[environment_container, agent_container],
            restart_policy="Never",
            volumes=volume_list,
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
    logger.info("Job created with status='%s'" % str(api_response.status))
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
    logger.info("Job deleted with status='%s'" % str(api_response.status))


def process_submission_callback(api_instance, body, challenge_phase, evalai):
    """Function to process submission message from SQS Queue

    Arguments:
        body {[dict]} -- Submission message body from AWS SQS Queue
        evalai {[EvalAI class object]} -- EvalAI class object imported from worker_utils
    """
    try:
        logger.info("[x] Received submission message %s" % body)
        environment_image = challenge_phase.get("environment_image")
        job = create_job_object(body, environment_image)
        response = create_job(api_instance, job)
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


def get_api_object(cluster_name, cluster_endpoint, challenge, evalai):
    configuration = client.Configuration()
    aws_eks_api = evalai.get_aws_eks_bearer_token(challenge.get("id"))
    configuration.host = cluster_endpoint
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = "/code/scripts/workers/certificate.crt"
    configuration.api_key["authorization"] = aws_eks_api[
        "aws_eks_bearer_token"
    ]
    configuration.api_key_prefix["authorization"] = "Bearer"
    api_instance = client.BatchV1Api(client.ApiClient(configuration))
    return api_instance


def get_api_client(cluster_name, cluster_endpoint, challenge, evalai):
    configuration = client.Configuration()
    aws_eks_api = evalai.get_aws_eks_bearer_token(challenge.get("id"))
    configuration.host = cluster_endpoint
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = "/code/scripts/workers/certificate.crt"
    configuration.api_key["authorization"] = aws_eks_api[
        "aws_eks_bearer_token"
    ]
    configuration.api_key_prefix["authorization"] = "Bearer"
    api_instance = client.ApiClient(configuration)
    return api_instance


def get_core_v1_api_object(cluster_name, cluster_endpoint, challenge, evalai):
    configuration = client.Configuration()
    aws_eks_api = evalai.get_aws_eks_bearer_token(challenge.get("id"))
    configuration.host = cluster_endpoint
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = "/code/scripts/workers/certificate.crt"
    configuration.api_key["authorization"] = aws_eks_api[
        "aws_eks_bearer_token"
    ]
    configuration.api_key_prefix["authorization"] = "Bearer"
    api_instance = client.CoreV1Api(client.ApiClient(configuration))
    return api_instance


def get_running_jobs(api_instance):
    """Function to get all the current jobs on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for deleting job
    """
    namespace = "default"
    try:
        api_response = api_instance.list_namespaced_job(namespace)
    except ApiException as e:
        logger.exception("Exception while receiving running Jobs{}".format(e))
    return api_response


def read_job(api_instance, job_name):
    """Function to get the status of a running job on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for deleting job
    """
    namespace = "default"
    try:
        api_response = api_instance.read_namespaced_job(job_name, namespace)
    except ApiException as e:
        logger.exception("Exception while reading Job with error {}".format(e))
    return api_response


def update_failed_jobs_and_send_logs(
    api_instance,
    core_v1_api_instance,
    evalai,
    job_name,
    submission_pk,
    challenge_pk,
    phase_pk,
):
    job_def = read_job(api_instance, job_name)
    controller_uid = job_def.metadata.labels["controller-uid"]
    pod_label_selector = "controller-uid=" + controller_uid
    pods_list = core_v1_api_instance.list_namespaced_pod(
        namespace="default",
        label_selector=pod_label_selector,
        timeout_seconds=10,
    )
    for container in pods_list.items[0].status.container_statuses:
        if container.name == "agent":
            if container.state.terminated is not None:
                if container.state.terminated.reason == "Error":
                    pod_name = pods_list.items[0].metadata.name
                    try:
                        pod_log_response = (
                            core_v1_api_instance.read_namespaced_pod_log(
                                name=pod_name,
                                namespace="default",
                                _return_http_data_only=True,
                                _preload_content=False,
                                container="agent",
                            )
                        )
                        pod_log = pod_log_response.data.decode("utf-8")
                        submission_data = {
                            "challenge_phase": phase_pk,
                            "submission": submission_pk,
                            "stdout": "",
                            "stderr": pod_log,
                            "submission_status": "FAILED",
                            "result": "[]",
                            "metadata": "",
                        }
                        response = evalai.update_submission_data(
                            submission_data, challenge_pk, phase_pk
                        )
                        print(response)
                    except client.rest.ApiException as e:
                        logger.exception(
                            "Exception while reading Job logs {}".format(e)
                        )


def install_gpu_drivers(api_instance):
    """Function to get the status of a running job on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating deamonset
    """
    logging.info("Installing Nvidia-GPU Drivers ...")
    link = "https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v1.11/nvidia-device-plugin.yml"  # pylint: disable=line-too-long
    logging.info("Using daemonset file: %s", link)
    nvidia_manifest = urllib.request.urlopen(link)
    daemonset_spec = yaml.load(nvidia_manifest, yaml.FullLoader)
    ext_client = client.ExtensionsV1beta1Api(api_instance)
    try:
        namespace = daemonset_spec["metadata"]["namespace"]
        ext_client.create_namespaced_daemon_set(namespace, daemonset_spec)
    except ApiException as e:
        if e.status == 409:
            logging.info(
                "Nvidia GPU driver daemon set has already been installed"
            )
        else:
            raise


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
    challenge = evalai.get_challenge_by_queue_name()
    cluster_details = evalai.get_aws_eks_cluster_details(challenge.get("id"))
    cluster_name = cluster_details.get("name")
    cluster_endpoint = cluster_details.get("cluster_endpoint")
    api_instance = get_api_client(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    install_gpu_drivers(api_instance)
    while True:
        message = evalai.get_message_from_sqs_queue()
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            challenge_pk = message_body.get("challenge_pk")
            phase_pk = message_body.get("phase_pk")
            submission = evalai.get_submission_by_pk(submission_pk)
            if submission:
                api_instance = get_api_object(
                    cluster_name, cluster_endpoint, challenge, evalai
                )
                core_v1_api_instance = get_core_v1_api_object(
                    cluster_name, cluster_endpoint, challenge, evalai
                )
                if (
                    submission.get("status") == "finished"
                    or submission.get("status") == "failed"
                    or submission.get("status") == "cancelled"
                ):
                    try:
                        # Fetch the last job name from the list as it is the latest running job
                        job_name = submission.get("job_name")[-1]
                        delete_job(api_instance, job_name)
                        message_receipt_handle = message.get("receipt_handle")
                        evalai.delete_message_from_sqs_queue(
                            message_receipt_handle
                        )
                    except Exception as e:
                        logger.exception(
                            "Failed to delete submission job: {}".format(e)
                        )
                        # Delete message from sqs queue to avoid re-triggering job delete
                        evalai.delete_message_from_sqs_queue(
                            message_receipt_handle
                        )
                elif submission.get("status") == "running":
                    job_name = submission.get("job_name")[-1]
                    update_failed_jobs_and_send_logs(
                        api_instance,
                        core_v1_api_instance,
                        evalai,
                        job_name,
                        submission_pk,
                        challenge_pk,
                        phase_pk,
                    )
                else:
                    logger.info(
                        "Processing message body: {0}".format(message_body)
                    )
                    challenge_phase = evalai.get_challenge_phase_by_pk(
                        challenge_pk, phase_pk
                    )
                    process_submission_callback(
                        api_instance, message_body, challenge_phase, evalai
                    )

        if killer.kill_now:
            break


if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
