import json
import logging
import os
import signal
import sys
import time

import yaml
from kubernetes import client

# TODO: Add exception in all the commands
from kubernetes.client.rest import ApiException
from statsd_utils import increment_and_push_metrics_to_statsd
from worker_utils import EvalAI_Interface


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "auth_token")
EVALAI_API_SERVER = os.environ.get(
    "EVALAI_API_SERVER", "http://localhost:8000"
)
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")
script_config_map_name = "evalai-scripts-cm"


def get_volume_mount_object(mount_path, name, read_only=False):
    volume_mount = client.V1VolumeMount(
        mount_path=mount_path, name=name, read_only=read_only
    )
    logger.info("Volume mount created at path: %s" % str(mount_path))
    return volume_mount


def get_volume_mount_list(mount_path, read_only=False):
    pvc_claim_name = "efs-claim"
    volume_mount = get_volume_mount_object(
        mount_path, pvc_claim_name, read_only
    )
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


def get_empty_volume_object(volume_name):
    empty_dir = client.V1EmptyDirVolumeSource()
    volume = client.V1Volume(empty_dir=empty_dir, name=volume_name)
    return volume


def get_config_map_volume_object(config_map_name, volume_name):
    config_map = client.V1ConfigMapVolumeSource(name=config_map_name)
    volume = client.V1Volume(config_map=config_map, name=volume_name)
    return volume


def create_config_map_object(config_map_name, file_paths):
    # Configure ConfigMap metadata
    metadata = client.V1ObjectMeta(
        name=config_map_name,
    )
    config_data = {}
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        file_content = open(file_path, "r").read()
        config_data[file_name] = file_content
    # Instantiate the config_map object
    config_map = client.V1ConfigMap(
        api_version="v1", kind="ConfigMap", data=config_data, metadata=metadata
    )
    return config_map


def create_configmap(core_v1_api_instance, config_map):
    try:
        config_maps = core_v1_api_instance.list_namespaced_config_map(
            namespace="default"
        )
        if (
            len(config_maps.items)
            and config_maps.items[0].metadata.name == script_config_map_name
        ):
            return
        core_v1_api_instance.create_namespaced_config_map(
            namespace="default",
            body=config_map,
        )
    except Exception as e:
        logger.exception(
            "Exception while creating configmap with error {}".format(e)
        )


def create_script_config_map(config_map_name):
    submission_script_file_path = (
        "/code/scripts/workers/code_upload_worker_utils/make_submission.sh"
    )
    monitor_submission_script_path = (
        "/code/scripts/workers/code_upload_worker_utils/monitor_submission.sh"
    )
    script_config_map = create_config_map_object(
        config_map_name,
        [submission_script_file_path, monitor_submission_script_path],
    )
    return script_config_map


def get_submission_meta_update_curl(submission_pk):
    url = "{}/api/jobs/submission/{}/update_started_at/".format(
        EVALAI_API_SERVER, submission_pk
    )
    curl_request = "curl --location --request PATCH '{}' --header 'Authorization: Bearer {}'".format(
        url, AUTH_TOKEN
    )
    return curl_request


def get_job_object(submission_pk, spec):
    """Function to instantiate the AWS EKS Job object

    Arguments:
        submission_pk {[int]} -- Submission id
        spec {[V1JobSpec]} -- Specification of deployment of job

    Returns:
        [AWS EKS Job class object] -- AWS EKS Job class object
    """

    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name="submission-{0}".format(submission_pk)
        ),
        spec=spec,
    )
    return job


def get_init_container(submission_pk):
    curl_request = get_submission_meta_update_curl(submission_pk)
    # Configure init container
    init_container = client.V1Container(
        name="init-container",
        image="ubuntu",
        command=[
            "/bin/bash",
            "-c",
            "apt update && apt install -y curl && {}".format(curl_request),
        ],
    )
    return init_container


def get_job_constraints(challenge):
    constraints = {}
    if not challenge.get("cpu_only_jobs"):
        constraints["nvidia.com/gpu"] = "1"
    else:
        constraints["cpu"] = challenge.get("job_cpu_cores")
        constraints["memory"] = challenge.get("job_memory")
    return constraints


def create_job_object(message, environment_image, challenge):
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
    submission_meta = message["submission_meta"]
    SUBMISSION_TIME_LIMIT_ENV = client.V1EnvVar(
        name="SUBMISSION_TIME_LIMIT",
        value=str(submission_meta["submission_time_limit"]),
    )
    # Configure Pod agent container
    agent_container = client.V1Container(
        name="agent", image=image, env=[PYTHONUNBUFFERED_ENV]
    )
    volume_mount_list = get_volume_mount_list("/dataset")
    job_constraints = get_job_constraints(challenge)
    # Get init container
    init_container = get_init_container(submission_pk)
    # Configure Pod environment container
    environment_container = client.V1Container(
        name="environment",
        image=environment_image,
        env=[
            PYTHONUNBUFFERED_ENV,
            AUTH_TOKEN_ENV,
            EVALAI_API_SERVER_ENV,
            MESSAGE_BODY_ENV,
            SUBMISSION_TIME_LIMIT_ENV,
        ],
        resources=client.V1ResourceRequirements(
            limits=job_constraints
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
    job = get_job_object(submission_pk, spec)
    return job


def create_static_code_upload_submission_job_object(message, challenge):
    """Function to create the static code upload pod AWS EKS Job object

    Arguments:
        message {[dict]} -- Submission message from AWS SQS queue
        challenge {challenges.Challenge} - Challenge model for the related challenge

    Returns:
        [AWS EKS Job class object] -- AWS EKS Job class object
    """

    PYTHONUNBUFFERED_ENV = client.V1EnvVar(name="PYTHONUNBUFFERED", value="1")
    # Used to create submission file by phase_pk and selecting dataset location
    submission_pk = message["submission_pk"]
    challenge_pk = message["challenge_pk"]
    phase_pk = message["phase_pk"]
    submission_meta = message["submission_meta"]
    SUBMISSION_PK_ENV = client.V1EnvVar(
        name="SUBMISSION_PK", value=str(submission_pk)
    )
    CHALLENGE_PK_ENV = client.V1EnvVar(
        name="CHALLENGE_PK", value=str(challenge_pk)
    )
    PHASE_PK_ENV = client.V1EnvVar(name="PHASE_PK", value=str(phase_pk))
    # Using Default value 1 day = 86400s as Time Limit.
    SUBMISSION_TIME_LIMIT_ENV = client.V1EnvVar(
        name="SUBMISSION_TIME_LIMIT",
        value=str(submission_meta["submission_time_limit"]),
    )
    SUBMISSION_TIME_DELTA_ENV = client.V1EnvVar(
        name="SUBMISSION_TIME_DELTA", value="300"
    )
    AUTH_TOKEN_ENV = client.V1EnvVar(name="AUTH_TOKEN", value=AUTH_TOKEN)
    EVALAI_API_SERVER_ENV = client.V1EnvVar(
        name="EVALAI_API_SERVER", value=EVALAI_API_SERVER
    )
    image = message["submitted_image_uri"]
    job_constraints = get_job_constraints(challenge)
    # Get init container
    init_container = get_init_container(submission_pk)
    # Get dataset volume and volume mounts
    volume_mount_list = get_volume_mount_list("/dataset", True)
    volume_list = get_volume_list()
    script_volume_name = "evalai-scripts"
    script_volume = get_config_map_volume_object(
        script_config_map_name, script_volume_name
    )
    volume_list.append(script_volume)
    script_volume_mount = get_volume_mount_object(
        "/evalai_scripts", script_volume_name, True
    )
    volume_mount_list.append(script_volume_mount)
    # Create and Mount submission Volume
    submission_path = "/submission"
    SUBMISSION_PATH_ENV = client.V1EnvVar(
        name="SUBMISSION_PATH", value=submission_path
    )
    submission_volume_name = "submissions-dir"
    submission_volume = get_empty_volume_object(submission_volume_name)
    volume_list.append(submission_volume)
    submission_volume_mount = get_volume_mount_object(
        submission_path, submission_volume_name
    )
    volume_mount_list.append(submission_volume_mount)
    # Configure Pod submission container
    submission_container = client.V1Container(
        name="submission",
        image=image,
        env=[
            PYTHONUNBUFFERED_ENV,
            SUBMISSION_PATH_ENV,
            CHALLENGE_PK_ENV,
            PHASE_PK_ENV,
        ],
        resources=client.V1ResourceRequirements(
            limits=job_constraints
        ),
        volume_mounts=volume_mount_list,
    )
    # Configure Pod sidecar container
    sidecar_container = client.V1Container(
        name="sidecar-container",
        image="ubuntu:latest",
        command=[
            "/bin/sh",
            "-c",
            "apt update && apt install -y curl && sh /evalai_scripts/monitor_submission.sh",
        ],
        env=[
            SUBMISSION_PATH_ENV,
            CHALLENGE_PK_ENV,
            PHASE_PK_ENV,
            SUBMISSION_PK_ENV,
            AUTH_TOKEN_ENV,
            EVALAI_API_SERVER_ENV,
            SUBMISSION_TIME_LIMIT_ENV,
            SUBMISSION_TIME_DELTA_ENV,
        ],
        volume_mounts=volume_mount_list,
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "evaluation"}),
        spec=client.V1PodSpec(
            init_containers=[init_container],
            containers=[sidecar_container, submission_container],
            restart_policy="Never",
            volumes=volume_list,
        ),
    )
    # Create the specification of deployment
    spec = client.V1JobSpec(backoff_limit=1, template=template)
    # Instantiate the job object
    job = get_job_object(submission_pk, spec)
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


def process_submission_callback(api_instance, body, challenge_phase, challenge, evalai):
    """Function to process submission message from SQS Queue

    Arguments:
        body {[dict]} -- Submission message body from AWS SQS Queue
        evalai {[EvalAI class object]} -- EvalAI class object imported from worker_utils
    """
    try:
        logger.info("[x] Received submission message %s" % body)
        if body.get("is_static_dataset_code_upload_submission"):
            job = create_static_code_upload_submission_job_object(body, challenge)
        else:
            environment_image = challenge_phase.get("environment_image")
            job = create_job_object(body, environment_image, challenge)
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
        return None
    return api_response


def cleanup_submission(
    api_instance,
    evalai,
    job_name,
    submission_pk,
    challenge_pk,
    phase_pk,
    stderr,
    environment_log,
    message,
    queue_name,
    is_remote,
):
    """Function to update status of submission to EvalAi, Delete corrosponding job from cluster and message from SQS.
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for deleting job
        evalai {[EvalAI class object]} -- EvalAI class object imported from worker_utils
        job_name {[string]} -- Name of the job to be terminated
        submission_pk {[int]} -- Submission id
        challenge_pk {[int]} -- Challenge id
        phase_pk {[int]} -- Challenge Phase id
        stderr {[string]} -- Reason of failure for submission/job
        environment_log {[string]} -- Reason of failure for submission/job from environment (code upload challenges only)
        message {[dict]} -- Submission message from AWS SQS queue
        queue_name {[string]} -- Submission SQS queue name
        is_remote {[int]} -- Whether the challenge is remote evaluation
    """
    try:
        submission_data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "stdout": "",
            "stderr": stderr,
            "environment_log": environment_log,
            "submission_status": "FAILED",
            "result": "[]",
            "metadata": "",
        }
        evalai.update_submission_data(submission_data, challenge_pk, phase_pk)
        try:
            delete_job(api_instance, job_name)
        except Exception as e:
            logger.exception("Failed to delete submission job: {}".format(e))
        message_receipt_handle = message.get("receipt_handle")
        if message_receipt_handle:
            evalai.delete_message_from_sqs_queue(message_receipt_handle)
            increment_and_push_metrics_to_statsd(queue_name, is_remote)
    except Exception as e:
        logger.exception(
            "Exception while cleanup Submission {}:  {}".format(
                submission_pk, e
            )
        )


def update_failed_jobs_and_send_logs(
    api_instance,
    core_v1_api_instance,
    evalai,
    job_name,
    submission_pk,
    challenge_pk,
    phase_pk,
    message,
    queue_name,
    is_remote,
    disable_logs
):
    clean_submission = False
    code_upload_environment_error = "Submission Job Failed."
    submission_error = "Submission Job Failed."
    try:
        job_def = read_job(api_instance, job_name)
        if job_def:
            controller_uid = job_def.metadata.labels["controller-uid"]
            pod_label_selector = "controller-uid=" + controller_uid
            pods_list = core_v1_api_instance.list_namespaced_pod(
                namespace="default",
                label_selector=pod_label_selector,
                timeout_seconds=10,
            )
            if disable_logs:
                code_upload_environment_error = None
                submission_error = None
            else:
                # Prevents monitoring when Job created with pending pods state (not assigned to node)
                if pods_list.items[0].status.container_statuses:
                    container_state_map = {}
                    for container in pods_list.items[0].status.container_statuses:
                        container_state_map[container.name] = container.state
                    for (
                        container_name,
                        container_state,
                    ) in container_state_map.items():
                        if container_name in ["agent", "submission", "environment"]:
                            if container_state.terminated is not None:
                                pod_name = pods_list.items[0].metadata.name
                                try:
                                    pod_log_response = core_v1_api_instance.read_namespaced_pod_log(
                                        name=pod_name,
                                        namespace="default",
                                        _return_http_data_only=True,
                                        _preload_content=False,
                                        container=container_name,
                                    )
                                    pod_log = pod_log_response.data.decode(
                                        "utf-8"
                                    )
                                    pod_log = pod_log[-10000:]
                                    clean_submission = True
                                    if container_name == "environment":
                                        code_upload_environment_error = pod_log
                                    else:
                                        submission_error = pod_log
                                except client.rest.ApiException as e:
                                    logger.exception(
                                        "Exception while reading Job logs {}".format(
                                            e
                                        )
                                    )
                else:
                    logger.info(
                        "Job pods in pending state, waiting for node assignment for submission {}".format(
                            submission_pk
                        )
                    )
        else:
            logger.exception(
                "Exception while reading Job {}, does not exist.".format(
                    job_name
                )
            )
            clean_submission = True
    except Exception as e:
        logger.exception("Exception while reading Job {}".format(e))
        clean_submission = True
    if clean_submission:
        cleanup_submission(
            api_instance,
            evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            submission_error,
            code_upload_environment_error,
            message,
            queue_name,
            is_remote,
        )


def install_gpu_drivers(api_instance):
    """Function to get the status of a running job on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating deamonset
    """
    logging.info("Installing Nvidia-GPU Drivers ...")
    # Original manifest source: https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v1.11/nvidia-device-plugin.yml
    manifest_path = "/code/scripts/workers/code_upload_worker_utils/nvidia-device-plugin.yml"
    logging.info("Using daemonset file: %s", manifest_path)
    nvidia_manifest = open(manifest_path).read()
    daemonset_spec = yaml.load(nvidia_manifest, yaml.FullLoader)
    ext_client = client.AppsV1Api(api_instance)
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
    is_remote = int(challenge.get("remote_evaluation"))
    cluster_details = evalai.get_aws_eks_cluster_details(challenge.get("id"))
    cluster_name = cluster_details.get("name")
    cluster_endpoint = cluster_details.get("cluster_endpoint")
    api_instance_client = get_api_client(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    # Install GPU drivers for GPU only challenges
    if not challenge.get("cpu_only_jobs"):
        install_gpu_drivers(api_instance_client)
    api_instance = get_api_object(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    core_v1_api_instance = get_core_v1_api_object(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    if challenge.get("is_static_dataset_code_upload"):
        # Create and Mount Script Volume
        script_config_map = create_script_config_map(script_config_map_name)
        create_configmap(core_v1_api_instance, script_config_map)
    submission_meta = {}
    submission_meta["submission_time_limit"] = challenge.get(
        "submission_time_limit"
    )
    while True:
        time.sleep(2)
        message = evalai.get_message_from_sqs_queue()
        message_body = message.get("body")
        if message_body:
            if challenge.get(
                "is_static_dataset_code_upload"
            ) and not message_body.get(
                "is_static_dataset_code_upload_submission"
            ):
                time.sleep(35)
                continue
            api_instance = get_api_object(
                cluster_name, cluster_endpoint, challenge, evalai
            )
            core_v1_api_instance = get_core_v1_api_object(
                cluster_name, cluster_endpoint, challenge, evalai
            )
            message_body["submission_meta"] = submission_meta
            submission_pk = message_body.get("submission_pk")
            challenge_pk = message_body.get("challenge_pk")
            phase_pk = message_body.get("phase_pk")
            challenge_phase = evalai.get_challenge_phase_by_pk(challenge_pk, phase_pk)
            disable_logs = challenge_phase.get("disable_logs")
            submission = evalai.get_submission_by_pk(submission_pk)
            if submission:
                if (
                    submission.get("status") == "finished"
                    or submission.get("status") == "failed"
                    or submission.get("status") == "cancelled"
                ):
                    try:
                        # Fetch the last job name from the list as it is the latest running job
                        job_name = submission.get("job_name")
                        if job_name:
                            latest_job_name = job_name[-1]
                            delete_job(api_instance, latest_job_name)
                        else:
                            logger.info(
                                "No job name found corresponding to submission: {} with status: {}."
                                "Deleting it from queue.".format(submission_pk, submission.get("status"))
                            )
                        message_receipt_handle = message.get("receipt_handle")
                        evalai.delete_message_from_sqs_queue(
                            message_receipt_handle
                        )
                        increment_and_push_metrics_to_statsd(
                            QUEUE_NAME, is_remote
                        )
                    except Exception as e:
                        logger.exception(
                            "Failed to delete submission job: {}".format(e)
                        )
                        # Delete message from sqs queue to avoid re-triggering job delete
                        evalai.delete_message_from_sqs_queue(
                            message_receipt_handle
                        )
                        increment_and_push_metrics_to_statsd(
                            QUEUE_NAME, is_remote
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
                        message,
                        QUEUE_NAME,
                        is_remote,
                        disable_logs,
                    )
                else:
                    logger.info(
                        "Processing message body: {0}".format(message_body)
                    )
                    challenge_phase = evalai.get_challenge_phase_by_pk(
                        challenge_pk, phase_pk
                    )
                    process_submission_callback(
                        api_instance, message_body, challenge_phase, challenge, evalai
                    )

        if killer.kill_now:
            break


if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
