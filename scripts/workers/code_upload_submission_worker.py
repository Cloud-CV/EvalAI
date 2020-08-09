import json
import logging
import os
import signal
import urllib
import yaml


from worker_utils import EvalAI_Interface

from kubernetes import client

# TODO: Add exception in all the commands
from kubernetes.client.rest import ApiException
from fluent_conf import fluent_conf, host_conf, systemd_conf


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
    # TODO: Add SSL verification
    configuration = client.Configuration()
    aws_eks_api = evalai.get_aws_eks_bearer_token(challenge.get("id"))
    configuration.host = cluster_endpoint
    configuration.verify_ssl = False
    configuration.api_key["authorization"] = aws_eks_api[
        "aws_eks_bearer_token"
    ]
    configuration.api_key_prefix["authorization"] = "Bearer"
    api_instance = client.BatchV1Api(client.ApiClient(configuration))
    return api_instance


def get_core_v1_api_object(cluster_name, challenge, evalai):
    configuration = client.Configuration()
    aws_eks_api = evalai.get_aws_eks_bearer_token(challenge.get("id"))
    configuration.api_key["authorization"] = aws_eks_api[
        "aws_eks_bearer_token"
    ]
    configuration.api_key_prefix["authorization"] = "Bearer"
    api_instance = client.CoreV1Api(client.ApiClient(configuration))
    return api_instance


def get_rbac_authorization_V1_api_object(cluster_name, challenge, evalai):
    configuration = client.Configuration()
    aws_eks_api = evalai.get_aws_eks_bearer_token(challenge.get("id"))
    configuration.api_key["authorization"] = aws_eks_api[
        "aws_eks_bearer_token"
    ]
    configuration.api_key_prefix["authorization"] = "Bearer"
    api_instance = client.RbacAuthorizationV1Api(
        client.ApiClient(configuration)
    )
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
                        pod_log_response = core_v1_api_instance.read_namespaced_pod_log(
                            name=pod_name,
                            namespace="default",
                            _return_http_data_only=True,
                            _preload_content=False,
                            container="agent",
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
    nvidia_manifest = urllib.urlopen(link)
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


def create_namespace(api_instance):
    """Function to create a namespace on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating namespace
    """
    body = client.V1Namespace(
        api_version="v1",
        kind="Namespace",
        metadata=client.V1ObjectMeta(
            name="amazon-cloudwatch", labels={"name": "amazon-cloudwatch"}
        ),
    )
    try:
        api_instance.create_namespace(body)
    except ApiException as e:
        if e.status == 409:
            logging.info("Namespace Already created")
        else:
            raise


def create_service_account(api_instance):
    """Function to create a service_account on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating service_account
    """
    namespace = "amazon-cloudwatch"
    body = client.V1ServiceAccount(
        api_version="v1",
        kind="ServiceAccount",
        metadata=client.V1ObjectMeta(name="fluentd"),
    )
    try:
        api_instance.create_namespaced_service_account(
            namespace=namespace, body=body,
        )
    except ApiException as e:
        if e.status == 409:
            logging.info("Service Account Already created")
        else:
            raise


def create_cluster_role(api_instance):
    """Function to create a cluster_role on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating cluster_role
    """
    body = client.V1ClusterRole(
        api_version="rbac.authorization.k8s.io/v1",
        kind="ClusterRole",
        metadata=client.V1ObjectMeta(name="fluentd-role"),
        rules=client.V1PolicyRule(
            api_groups=[""],
            resources=["namespaces", "pods", "pods/logs"],
            verbs=["get", "list", "watch"],
        ),
    )
    try:
        api_instance.create_cluster_role(body=body)
    except ApiException as e:
        if e.status == 409:
            logging.info("cluster_role Already created")
        else:
            raise


def create_cluster_role_binding(api_instance):
    """Function to create a cluster_role_binding on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating cluster_role_binding
    """
    body = client.V1ClusterRoleBinding(
        api_version="rbac.authorization.k8s.io/v1",
        kind="ClusterRoleBinding",
        metadata=client.V1ObjectMeta(name="fluentd-role-binding"),
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name="fluentd-role",
        ),
        subjects=client.V1Subject(
            kind="ServiceAccount",
            name="fluentd",
            namespace="amazon-cloudwatch",
        ),
    )
    try:
        api_instance.create_cluster_role_binding(body)
    except ApiException as e:
        if e.status == 409:
            logging.info("cluster_role_binding Already created")
        else:
            raise


def create_config_map(api_instance):
    """Function to create a config_map on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating config_map
    """
    namespace = "amazon-cloudwatch"
    body = client.client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(
            name="fluentd-config",
            namespace="amazon-cloudwatch",
            labels={"k8s-app": "fluentd-cloudwatch"},
        ),
        data={
            "fluent.conf": fluent_conf,
            "systemd.conf": systemd_conf,
            "host.conf": host_conf,
        },
    )
    api_instance.create_namespaced_config_map(namespace, body)
    try:
        api_instance.create_namespaced_config_map(namespace, body)
    except ApiException as e:
        if e.status == 409:
            logging.info("Configmap Already created")
        else:
            raise


def install_fluentd(api_instance):
    """Function to get the status of a running job on AWS EKS cluster
    Arguments:
        api_instance {[AWS EKS API object]} -- API object for creating deamonset
    """
    logging.info("Installing Fluentd ...")
    fluentd_manifest = """
        apiVersion: apps/v1
        kind: DaemonSet
        metadata:
        name: fluentd-cloudwatch
        namespace: amazon-cloudwatch
        spec:
        selector:
            matchLabels:
            k8s-app: fluentd-cloudwatch
        template:
            metadata:
            labels:
                k8s-app: fluentd-cloudwatch
            annotations:
                configHash: 8915de4cf9c3551a8dc74c0137a3e83569d28c71044b0359c2578d2e0461825
            spec:
            serviceAccountName: fluentd
            terminationGracePeriodSeconds: 30
            # Because the image's entrypoint requires to write on /fluentd/etc but we mount configmap there which is read-only,
            # this initContainers workaround or other is needed.
            # See https://github.com/fluent/fluentd-kubernetes-daemonset/issues/90
            initContainers:
                - name: copy-fluentd-config
                image: busybox
                command: ['sh', '-c', 'cp /config-volume/..data/* /fluentd/etc']
                volumeMounts:
                    - name: config-volume
                    mountPath: /config-volume
                    - name: fluentdconf
                    mountPath: /fluentd/etc
                - name: update-log-driver
                image: busybox
                command: ['sh','-c','']
            containers:
                - name: fluentd-cloudwatch
                image: fluent/fluentd-kubernetes-daemonset:v1.7.3-debian-cloudwatch-1.0
                env:
                    - name: REGION
                    valueFrom:
                        configMapKeyRef:
                        name: cluster-info
                        key: logs.region
                    - name: CLUSTER_NAME
                    valueFrom:
                        configMapKeyRef:
                        name: cluster-info
                        key: cluster.name
                    - name: CI_VERSION
                    value: "k8s/1.1.1"
                resources:
                    limits:
                    memory: 400Mi
                    requests:
                    cpu: 100m
                    memory: 200Mi
                volumeMounts:
                    - name: config-volume
                    mountPath: /config-volume
                    - name: fluentdconf
                    mountPath: /fluentd/etc
                    - name: varlog
                    mountPath: /var/log
                    - name: varlibdockercontainers
                    mountPath: /var/lib/docker/containers
                    readOnly: true
                    - name: runlogjournal
                    mountPath: /run/log/journal
                    readOnly: true
                    - name: dmesg
                    mountPath: /var/log/dmesg
                    readOnly: true
            volumes:
                - name: config-volume
                configMap:
                    name: fluentd-config
                - name: fluentdconf
                emptyDir: {}
                - name: varlog
                hostPath:
                    path: /var/log
                - name: varlibdockercontainers
                hostPath:
                    path: /var/lib/docker/containers
                - name: runlogjournal
                hostPath:
                    path: /run/log/journal
                - name: dmesg
                hostPath:
                    path: /var/log/dmesg
    """
    daemonset_spec = yaml.load(fluentd_manifest, yaml.FullLoader)
    ext_client = client.ExtensionsV1beta1Api(api_instance)
    try:
        namespace = daemonset_spec["metadata"]["namespace"]
        ext_client.create_namespaced_daemon_set(namespace, daemonset_spec)
    except ApiException as e:
        if e.status == 409:
            logging.info("Fluentd has already been installed")
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
    api_instance = get_api_object(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    core_v1_api_instance = get_core_v1_api_object(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    rbac_authorization_V1_api_instance = get_rbac_authorization_V1_api_object(
        cluster_name, cluster_endpoint, challenge, evalai
    )
    install_gpu_drivers(api_instance)
    # installing fluentd
    create_namespace(core_v1_api_instance)
    create_service_account(core_v1_api_instance)
    create_cluster_role(rbac_authorization_V1_api_instance)
    create_cluster_role_binding(rbac_authorization_V1_api_instance)
    create_config_map(core_v1_api_instance)
    install_fluentd(api_instance)

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

                if (
                    submission.get("status") == "finished"
                    or submission.get("status") == "failed"
                    or submission.get("status") == "cancelled"
                ):
                    # Fetch the last job name from the list as it is the latest
                    # running job
                    job_name = submission.get("job_name")[-1]
                    delete_job(api_instance, job_name)
                    message_receipt_handle = message.get("receipt_handle")
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
