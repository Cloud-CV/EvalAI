from __future__ import print_function
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint

# Configure API key authorization: BearerToken
# configuration = kubernetes.client.Configuration()
# configuration.api_key['authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['authorization'] = 'Bearer'

# create an instance of the API class
config.load_kube_config()
api_instance = client.AppsV1Api()
namespace = "default"  # str | object name and auth scope, such as for teams and projects
metadata = client.V1ObjectMeta(
    name="nvidia-device-plugin-daemonset", namespace="kube-system"
)
selector = client.V1LabelSelector(
    match_labels={"name": "nvidia-device-plugin-ds"}
)
rolling_update = client.V1RollingUpdateDaemonSet()
update_strategy = client.V1DaemonSetUpdateStrategy(type=rolling_update)
template_metadata = client.V1ObjectMeta(
    annotations={"scheduler.alpha.kubernetes.io/critical-pod": ""},
    labels={"name": "nvidia-device-plugin-ds"},
)
tolerations = client.V1Toleration(
    key="CriticalAddonsOnly",
    operator="Exists",
    # key="nvidia.com/gpu",
    # operator="Exists",
    effect="NoSchedule",
)
capabilities = client.V1Capabilities(drop=["ALL"])
security_context = client.V1SecurityContext(
    allow_privilege_escalation=False, capabilities=capabilities,
)
volume_mounts = client.V1VolumeMount(
    name="device-plugin", mount_path="/var/lib/kubelet/device-plugins"
)
host_path = client.V1HostPathVolumeSource(
    path="/var/lib/kubelet/device-plugins"
)
volumes = client.V1Volume(name="device-plugin", host_path=host_path)
containers = client.V1Container(
    image="nvidia/k8s-device-plugin:1.0.0-beta6",
    name="nvidia-device-plugin-ctr",
    security_context=security_context,
    volume_mounts=volume_mounts,
)
template_specs = client.V1PodSpec(
    tolerations=tolerations,
    priority_class_name="system-node-critical",
    containers=containers,
    volumes=volumes,
)
template = client.V1PodTemplateSpec(
    metadata=template_metadata, spec=template_specs
)
spec = client.V1DaemonSetSpec(
    selector=selector, update_strategy=update_strategy, template=template
)
body = client.V1DaemonSet(
    api_version="apps/v1", kind="DaemonSet", metadata=metadata, spec=spec
)  # V1DaemonSet |

try:
    api_response = api_instance.create_namespaced_daemon_set(namespace, body)
    pprint(api_response)
except ApiException as e:
    print(
        "Exception when calling AppsV1Api->create_namespaced_daemon_set: %s\n"
        % e
    )
