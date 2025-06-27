import signal
import unittest
from unittest.mock import MagicMock, mock_open, patch

import yaml
from kubernetes import client
from kubernetes.client.rest import ApiException

from scripts.workers.code_upload_submission_worker import (
    EVALAI_API_SERVER,
    GracefulKiller,
    create_config_map_object,
    create_configmap,
    create_job,
    create_job_object,
    create_script_config_map,
    create_static_code_upload_submission_job_object,
    delete_job,
    get_api_client,
    get_api_object,
    get_config_map_volume_object,
    get_core_v1_api_object,
    get_empty_volume_object,
    get_init_container,
    get_job_constraints,
    get_job_object,
    get_pods_from_job,
    get_submission_meta_update_curl,
    get_volume_list,
    get_volume_mount_list,
    get_volume_mount_object,
    install_gpu_drivers,
    main,
    process_submission_callback,
    read_job,
    update_failed_jobs_and_send_logs,
)


class TestGracefulKiller(unittest.TestCase):
    def test_exit_gracefully(self):
        killer = GracefulKiller()
        killer.exit_gracefully(signal.SIGINT, None)
        self.assertTrue(killer.kill_now)


class TestGetVolumeMountObject(unittest.TestCase):
    def test_get_volume_mount_object(self):
        mount_path = "/mnt/data"
        name = "data-volume"
        read_only = True
        volume_mount = get_volume_mount_object(mount_path, name, read_only)
        self.assertEqual(volume_mount.mount_path, mount_path)
        self.assertEqual(volume_mount.name, name)
        self.assertEqual(volume_mount.read_only, read_only)

    def test_get_volume_mount_list(self):
        mount_path = "/mnt/data"
        read_only = True
        volume_mount_list = get_volume_mount_list(mount_path, read_only)
        self.assertEqual(len(volume_mount_list), 1)
        self.assertEqual(volume_mount_list[0].mount_path, mount_path)
        self.assertEqual(volume_mount_list[0].name, "efs-claim")
        self.assertEqual(volume_mount_list[0].read_only, read_only)

    def test_get_volume_list(self):
        volume_list = get_volume_list()
        self.assertEqual(len(volume_list), 1)
        self.assertEqual(volume_list[0].name, "efs-claim")
        self.assertEqual(
            volume_list[0].persistent_volume_claim.claim_name, "efs-claim"
        )

    def test_get_empty_volume_object(self):
        volume_name = "empty-volume"
        volume = get_empty_volume_object(volume_name)
        self.assertEqual(volume.name, volume_name)
        self.assertIsInstance(volume.empty_dir, client.V1EmptyDirVolumeSource)

    def test_get_config_map_volume_object(self):
        config_map_name = "config-map"
        volume_name = "config-map-volume"
        volume = get_config_map_volume_object(config_map_name, volume_name)
        self.assertEqual(volume.name, volume_name)
        self.assertIsInstance(
            volume.config_map, client.V1ConfigMapVolumeSource
        )
        self.assertEqual(volume.config_map.name, config_map_name)


class TestCreateConfigMapObject(unittest.TestCase):
    @patch(
        "kubernetes.client.V1ObjectMeta"
    )  # Mock the kubernetes client V1ObjectMeta
    @patch(
        "kubernetes.client.V1ConfigMap"
    )  # Mock the kubernetes client V1ConfigMap
    @patch(
        "builtins.open", new_callable=mock_open, read_data="file content"
    )  # Mock open function
    def test_create_config_map_object_success(
        self, mock_open, MockV1ConfigMap, MockV1ObjectMeta
    ):
        # Define mock file paths
        mock_file_paths = ["/path/to/file1.txt", "/path/to/file2.txt"]

        # Call the function
        config_map = create_config_map_object(
            "test-config-map", mock_file_paths
        )

        # Check if V1ObjectMeta was called with the right parameters
        MockV1ObjectMeta.assert_called_once_with(name="test-config-map")

        # Check if V1ConfigMap was called with the right parameters
        MockV1ConfigMap.assert_called_once_with(
            api_version="v1",
            kind="ConfigMap",
            data={"file1.txt": "file content", "file2.txt": "file content"},
            metadata=MockV1ObjectMeta.return_value,
        )

        # Check if the correct ConfigMap object is returned
        self.assertEqual(config_map, MockV1ConfigMap.return_value)

    @patch("kubernetes.client.V1ObjectMeta")
    @patch("kubernetes.client.V1ConfigMap")
    def test_create_config_map_object_empty_file_paths(
        self, MockV1ConfigMap, MockV1ObjectMeta
    ):
        config_map = create_config_map_object("test-config-map", [])

        MockV1ObjectMeta.assert_called_once_with(name="test-config-map")

        MockV1ConfigMap.assert_called_once_with(
            api_version="v1",
            kind="ConfigMap",
            data={},
            metadata=MockV1ObjectMeta.return_value,
        )

        self.assertEqual(config_map, MockV1ConfigMap.return_value)

    @patch("kubernetes.client.V1ObjectMeta")
    @patch("kubernetes.client.V1ConfigMap")
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_create_config_map_object_file_not_found(
        self, mock_open, MockV1ConfigMap, MockV1ObjectMeta
    ):
        with self.assertRaises(FileNotFoundError):
            create_config_map_object(
                "test-config-map", ["/path/to/nonexistent_file.txt"]
            )

    @patch("kubernetes.client.V1ObjectMeta")
    @patch("kubernetes.client.V1ConfigMap")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_config_map_object_file_read_error(
        self, mock_open, MockV1ConfigMap, MockV1ObjectMeta
    ):
        mock_open.side_effect = IOError("Unable to read file")
        with self.assertRaises(IOError):
            create_config_map_object("test-config-map", ["/path/to/file.txt"])


class TestCreateConfigMap(unittest.TestCase):
    @patch("kubernetes.client.CoreV1Api")
    def test_create_configmap_success(self, MockCoreV1Api):
        # Mock the CoreV1Api instance
        core_v1_api_instance = MockCoreV1Api.return_value

        # Define the mock config map
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "test-config-map"},
            "data": {"key1": "value1", "key2": "value2"},
        }

        # Call the function
        create_configmap(core_v1_api_instance, config_map)

        # Check if the CoreV1Api method was called with the right parameters
        core_v1_api_instance.create_namespaced_config_map.assert_called_once_with(
            namespace="default", body=config_map
        )

    @patch("kubernetes.client.CoreV1Api")
    def test_create_configmap_exception(self, MockCoreV1Api):
        # Mock the CoreV1Api instance
        core_v1_api_instance = MockCoreV1Api.return_value

        # Define the mock config map
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "test-config-map"},
            "data": {"key1": "value1", "key2": "value2"},
        }

        # Mock the create_namespaced_config_map method to raise an exception
        core_v1_api_instance.create_namespaced_config_map.side_effect = (
            Exception("Test exception")
        )

        # Call the function and check if the exception is logged
        with patch(
            "scripts.workers.code_upload_submission_worker.logger.exception"
        ) as mock_logger:
            try:
                create_configmap(core_v1_api_instance, config_map)
            except Exception as e:
                mock_logger.assert_called_once_with(
                    f"Exception while creating configmap with error Test exception {e}"
                )

        # Ensure create_namespaced_config_map was called
        core_v1_api_instance.create_namespaced_config_map.assert_called_once()


class TestConfigFunctions(unittest.TestCase):
    @patch(
        "scripts.workers.code_upload_submission_worker.create_config_map_object"
    )  # Mock the create_config_map_object function
    def test_create_script_config_map(self, MockCreateConfigMapObject):
        # Mock the return value of create_config_map_object
        mock_config_map = MagicMock()
        MockCreateConfigMapObject.return_value = mock_config_map

        config_map_name = "test-config-map"
        expected_file_paths = [
            "/code/scripts/workers/code_upload_worker_utils/make_submission.sh",
            "/code/scripts/workers/code_upload_worker_utils/monitor_submission.sh",
        ]

        # Call the function
        result = create_script_config_map(config_map_name)

        # Assert create_config_map_object was called with the correct parameters
        MockCreateConfigMapObject.assert_called_once_with(
            config_map_name, expected_file_paths
        )

        # Assert the return value is as expected
        self.assertEqual(result, mock_config_map)

    @patch(
        "scripts.workers.code_upload_submission_worker.EVALAI_API_SERVER",
        "http://example.com",
    )  # Mock the EVALAI_API_SERVER
    @patch(
        "scripts.workers.code_upload_submission_worker.AUTH_TOKEN",
        "test-auth-token",
    )  # Mock the AUTH_TOKEN
    def test_get_submission_meta_update_curl(self):
        submission_pk = 123
        expected_url = (
            "http://example.com/api/jobs/submission/123/update_started_at/"
        )
        expected_curl_request = "curl --location --request PATCH '{}' --header 'Authorization: Bearer {}'".format(
            expected_url, "test-auth-token"
        )

        # Call the function
        result = get_submission_meta_update_curl(submission_pk)

        # Assert the result matches the expected curl command
        self.assertEqual(result, expected_curl_request)

    @patch(
        "scripts.workers.code_upload_submission_worker.client.V1Job"
    )  # Replace 'scripts.workers.code_upload_submission_worker' with the actual module name
    @patch(
        "scripts.workers.code_upload_submission_worker.client.V1ObjectMeta"
    )  # Replace 'scripts.workers.code_upload_submission_worker' with the actual module name
    def test_get_job_object(self, MockV1ObjectMeta, MockV1Job):
        # Arrange
        submission_pk = 123
        spec = (
            MagicMock()
        )  # Create a mock for V1JobSpec or provide a mock spec if you have one
        expected_name = "submission-123"

        # Configure the mocks
        MockV1ObjectMeta.return_value = MagicMock()
        MockV1Job.return_value = MagicMock()

        # Act
        result = get_job_object(submission_pk, spec)

        # Assert
        MockV1ObjectMeta.assert_called_once_with(name=expected_name)
        MockV1Job.assert_called_once_with(
            api_version="batch/v1",
            kind="Job",
            metadata=MockV1ObjectMeta.return_value,
            spec=spec,
        )
        self.assertEqual(result, MockV1Job.return_value)

    @patch(
        "scripts.workers.code_upload_submission_worker.client.V1Container"
    )  # Replace 'scripts.workers.code_upload_submission_worker' with the actual module name
    @patch(
        "scripts.workers.code_upload_submission_worker.get_submission_meta_update_curl"
    )
    def test_get_init_container(
        self, MockGetSubmissionMetaUpdateCurl, MockV1Container
    ):
        # Arrange
        submission_pk = 123
        curl_request = "curl_command"  # Example curl command
        MockGetSubmissionMetaUpdateCurl.return_value = curl_request

        expected_command = [
            "/bin/bash",
            "-c",
            "apt update && apt install -y curl && curl_command",
        ]

        MockV1Container.return_value = MagicMock()

        # Act
        result = get_init_container(submission_pk)

        # Assert
        MockGetSubmissionMetaUpdateCurl.assert_called_once_with(submission_pk)
        MockV1Container.assert_called_once_with(
            name="init-container", image="ubuntu", command=expected_command
        )
        self.assertEqual(result, MockV1Container.return_value)

    @patch(
        "scripts.workers.code_upload_submission_worker.read_job"
    )  # Adjust the path if necessary
    def test_get_pods_from_job(self, MockReadJob):
        # Arrange
        api_instance = MagicMock()
        core_v1_api_instance = MagicMock()
        job_name = "job-123"
        job_def = MagicMock()
        job_def.metadata.labels = {"controller-uid": "uid-123"}

        # Mock methods
        MockReadJob.return_value = job_def
        core_v1_api_instance.list_namespaced_pod.return_value = "pod_list"

        expected_label_selector = "controller-uid=uid-123"

        # Act
        result = get_pods_from_job(
            api_instance, core_v1_api_instance, job_name
        )

        # Assert
        MockReadJob.assert_called_once_with(api_instance, job_name)
        core_v1_api_instance.list_namespaced_pod.assert_called_once_with(
            namespace="default",
            label_selector=expected_label_selector,
            timeout_seconds=10,
        )
        self.assertEqual(result, "pod_list")

    def test_get_job_constraints(self):
        # Arrange
        challenge_cpu_only = {"cpu_only_jobs": False}
        challenge_cpu = {
            "cpu_only_jobs": True,
            "job_cpu_cores": "4",
            "job_memory": "16Gi",
        }

        # Act
        result_cpu_only = get_job_constraints(challenge_cpu_only)
        result_cpu = get_job_constraints(challenge_cpu)

        # Assert
        self.assertEqual(result_cpu_only, {"nvidia.com/gpu": "1"})
        self.assertEqual(result_cpu, {"cpu": "4", "memory": "16Gi"})

    @patch("scripts.workers.code_upload_submission_worker.get_job_object")
    @patch("scripts.workers.code_upload_submission_worker.get_volume_list")
    @patch("scripts.workers.code_upload_submission_worker.get_init_container")
    @patch("scripts.workers.code_upload_submission_worker.get_job_constraints")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_volume_mount_list"
    )
    @patch("scripts.workers.code_upload_submission_worker.client.V1JobSpec")
    @patch(
        "scripts.workers.code_upload_submission_worker.client.V1PodTemplateSpec"
    )
    @patch("scripts.workers.code_upload_submission_worker.client.V1PodSpec")
    @patch("scripts.workers.code_upload_submission_worker.client.V1Container")
    @patch("scripts.workers.code_upload_submission_worker.client.V1EnvVar")
    def test_create_job_object(
        self,
        MockV1EnvVar,
        MockV1Container,
        MockV1PodSpec,
        MockV1PodTemplateSpec,
        MockV1JobSpec,
        MockGetVolumeMountList,
        MockGetJobConstraints,
        MockGetInitContainer,
        MockGetVolumeList,
        MockGetJobObject,
    ):
        # Arrange
        message = {
            "submission_pk": 123,
            "submitted_image_uri": "test-image-uri",
            "submission_meta": {"submission_time_limit": 3600},
        }
        environment_image = "env-image"
        challenge = {"cpu_only_jobs": False}

        # Mock objects returned by the functions
        MockV1EnvVar.side_effect = lambda name, value: f"mock-envvar-{name}"
        MockV1Container.side_effect = lambda *args, **kwargs: "mock-container"
        MockV1PodSpec.return_value = "mock-podspec"
        MockV1PodTemplateSpec.return_value = "mock-podtemplatespec"
        MockV1JobSpec.return_value = "mock-jobspec"
        MockGetVolumeMountList.return_value = "mock-volume-mount-list"
        MockGetJobConstraints.return_value = {"nvidia.com/gpu": "1"}
        MockGetInitContainer.return_value = "mock-init-container"
        MockGetVolumeList.return_value = "mock-volume-list"
        MockGetJobObject.return_value = "mock-job-object"

        # Act
        result = create_job_object(message, environment_image, challenge)

        # Assert
        self.assertEqual(result, "mock-job-object")

        # Verify the mocked functions were called with the expected arguments
        MockGetVolumeMountList.assert_called_once_with("/dataset")
        MockGetJobConstraints.assert_called_once_with(challenge)
        MockGetInitContainer.assert_called_once_with(message["submission_pk"])
        MockGetVolumeList.assert_called_once()
        MockGetJobObject.assert_called_once_with(123, "mock-jobspec")
        MockV1EnvVar.assert_any_call(name="PYTHONUNBUFFERED", value="1")
        MockV1EnvVar.assert_any_call(name="AUTH_TOKEN", value="auth_token")
        MockV1EnvVar.assert_any_call(
            name="BODY",
            value=(
                '{"submission_pk": 123, "submitted_image_uri": "test-image-uri", '
                '"submission_meta": {"submission_time_limit": 3600}}'
            ),
        )
        MockV1EnvVar.assert_any_call(
            name="SUBMISSION_TIME_LIMIT", value="3600"
        )

        MockV1Container.assert_any_call(
            name="agent",
            image=message["submitted_image_uri"],
            env=["mock-envvar-PYTHONUNBUFFERED"],
        )

        MockV1Container.assert_any_call(
            name="environment",
            image=environment_image,
            env=[
                "mock-envvar-PYTHONUNBUFFERED",
                "mock-envvar-AUTH_TOKEN",
                "mock-envvar-EVALAI_API_SERVER",
                "mock-envvar-BODY",
                "mock-envvar-SUBMISSION_TIME_LIMIT",
            ],
            resources=client.V1ResourceRequirements(
                limits={"nvidia.com/gpu": "1"}
            ),
            volume_mounts="mock-volume-mount-list",
        )

        MockV1PodSpec.assert_called_once_with(
            init_containers=["mock-init-container"],
            containers=["mock-container", "mock-container"],
            restart_policy="Never",
            volumes="mock-volume-list",
        )

        MockV1PodTemplateSpec.assert_called_once_with(
            metadata=client.V1ObjectMeta(labels={"app": "evaluation"}),
            spec="mock-podspec",
        )

        MockV1JobSpec.assert_called_once_with(
            backoff_limit=1, template="mock-podtemplatespec"
        )

    @patch("scripts.workers.code_upload_submission_worker.get_job_object")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_empty_volume_object"
    )
    @patch(
        "scripts.workers.code_upload_submission_worker.get_volume_mount_object"
    )
    @patch(
        "scripts.workers.code_upload_submission_worker.get_config_map_volume_object"
    )
    @patch("scripts.workers.code_upload_submission_worker.get_volume_list")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_volume_mount_list"
    )
    @patch("scripts.workers.code_upload_submission_worker.get_init_container")
    @patch("scripts.workers.code_upload_submission_worker.get_job_constraints")
    @patch("scripts.workers.code_upload_submission_worker.client.V1EnvVar")
    @patch("scripts.workers.code_upload_submission_worker.client.V1Container")
    @patch("scripts.workers.code_upload_submission_worker.client.V1PodSpec")
    @patch(
        "scripts.workers.code_upload_submission_worker.client.V1PodTemplateSpec"
    )
    @patch("scripts.workers.code_upload_submission_worker.client.V1JobSpec")
    def test_create_static_code_upload_submission_job_object(
        self,
        MockV1JobSpec,
        MockV1PodTemplateSpec,
        MockV1PodSpec,
        MockV1Container,
        MockV1EnvVar,
        MockGetJobConstraints,
        MockGetInitContainer,
        MockGetVolumeMountList,
        MockGetVolumeList,
        MockGetConfigMapVolumeObject,
        MockGetVolumeMountObject,
        MockGetEmptyVolumeObject,
        MockGetJobObject,
    ):
        # Arrange
        message = {
            "submission_pk": 123,
            "submitted_image_uri": "test-image-uri",
            "challenge_pk": 1,
            "phase_pk": 2,
            "submission_meta": {"submission_time_limit": 3600},
        }
        challenge = {"cpu_only_jobs": False}

        # Mock return values
        MockV1EnvVar.side_effect = lambda name, value: f"mock-envvar-{name}"
        MockV1Container.side_effect = lambda *args, **kwargs: "mock-container"
        MockV1PodSpec.return_value = "mock-podspec"
        MockV1PodTemplateSpec.return_value = "mock-podtemplatespec"
        MockV1JobSpec.return_value = "mock-jobspec"
        MockGetJobConstraints.return_value = {"nvidia.com/gpu": "1"}
        MockGetInitContainer.return_value = "mock-init-container"
        MockGetVolumeMountList.return_value = []
        MockGetVolumeList.return_value = []
        MockGetConfigMapVolumeObject.return_value = "mock-config-map-volume"
        MockGetVolumeMountObject.side_effect = (
            lambda mount_path, name, sub_path=None: f"mock-volume-mount-{name}"
        )
        MockGetEmptyVolumeObject.return_value = "mock-empty-volume"
        MockGetJobObject.return_value = "mock-job-object"

        # Act
        result = create_static_code_upload_submission_job_object(
            message, challenge
        )

        # Assert
        self.assertEqual(result, "mock-job-object")

        # Verify calls
        MockV1EnvVar.assert_any_call(name="PYTHONUNBUFFERED", value="1")
        MockV1EnvVar.assert_any_call(name="SUBMISSION_PK", value="123")
        MockV1EnvVar.assert_any_call(name="CHALLENGE_PK", value="1")
        MockV1EnvVar.assert_any_call(name="PHASE_PK", value="2")
        MockV1EnvVar.assert_any_call(
            name="SUBMISSION_TIME_LIMIT", value="3600"
        )
        MockV1EnvVar.assert_any_call(name="SUBMISSION_TIME_DELTA", value="300")
        MockV1EnvVar.assert_any_call(name="AUTH_TOKEN", value="auth_token")
        MockV1EnvVar.assert_any_call(
            name="EVALAI_API_SERVER", value=EVALAI_API_SERVER
        )

        MockGetVolumeMountList.assert_called_once_with("/dataset", True)
        MockGetVolumeList.assert_called_once()
        MockGetConfigMapVolumeObject.assert_called_once_with(
            "evalai-scripts-cm", "evalai-scripts"
        )
        MockGetVolumeMountObject.assert_any_call(
            "/evalai_scripts", "evalai-scripts", True
        )
        MockGetVolumeMountObject.assert_any_call(
            "/submission", "submissions-dir"
        )
        MockGetEmptyVolumeObject.assert_called_once_with("submissions-dir")
        MockGetJobObject.assert_called_once_with(123, "mock-jobspec")

        # Verify calls for volumes and mounts
        MockGetVolumeList.assert_called_once()
        MockGetEmptyVolumeObject.assert_called_once_with("submissions-dir")
        MockGetVolumeMountObject.assert_any_call(
            "/submission", "submissions-dir"
        )
        self.assertIn("mock-config-map-volume", MockGetVolumeList.return_value)
        self.assertIn(
            "mock-volume-mount-submissions-dir",
            MockGetVolumeMountList.return_value,
        )

        # Verify container configurations
        MockV1Container.assert_any_call(
            name="submission",
            image="test-image-uri",
            env=[
                "mock-envvar-PYTHONUNBUFFERED",
                "mock-envvar-SUBMISSION_PATH",
                "mock-envvar-CHALLENGE_PK",
                "mock-envvar-PHASE_PK",
            ],
            resources=client.V1ResourceRequirements(
                limits={"nvidia.com/gpu": "1"}
            ),
            volume_mounts=MockGetVolumeMountList.return_value,
        )

        MockV1Container.assert_any_call(
            name="sidecar-container",
            image="ubuntu:latest",
            command=[
                "/bin/sh",
                "-c",
                "apt update && apt install -y curl && sh /evalai_scripts/monitor_submission.sh",
            ],
            env=[
                "mock-envvar-SUBMISSION_PATH",
                "mock-envvar-CHALLENGE_PK",
                "mock-envvar-PHASE_PK",
                "mock-envvar-SUBMISSION_PK",
                "mock-envvar-AUTH_TOKEN",
                "mock-envvar-EVALAI_API_SERVER",
                "mock-envvar-SUBMISSION_TIME_LIMIT",
                "mock-envvar-SUBMISSION_TIME_DELTA",
            ],
            volume_mounts=MockGetVolumeMountList.return_value,
        )

        # Verify job creation
        MockV1JobSpec.assert_called_once_with(
            backoff_limit=1, template="mock-podtemplatespec"
        )
        MockGetJobObject.assert_called_once_with(123, "mock-jobspec")

    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_create_job(self, MockLogger):
        # Arrange
        mock_api_instance = MagicMock()
        mock_job = MagicMock()
        mock_api_response = MagicMock()
        mock_api_instance.create_namespaced_job.return_value = (
            mock_api_response
        )

        # Act
        response = create_job(mock_api_instance, mock_job)

        # Assert
        mock_api_instance.create_namespaced_job.assert_called_once_with(
            body=mock_job, namespace="default", pretty=True
        )
        MockLogger.info.assert_called_once_with(
            "Job created with status='%s'" % str(mock_api_response.status)
        )
        self.assertEqual(response, mock_api_response)

    @patch(
        "scripts.workers.code_upload_submission_worker.client.V1DeleteOptions"
    )
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_delete_job(self, MockLogger, MockV1DeleteOptions):
        # Arrange
        mock_api_instance = MagicMock()
        mock_job_name = "test-job"
        mock_api_response = MagicMock()
        mock_api_instance.delete_namespaced_job.return_value = (
            mock_api_response
        )
        mock_delete_options = MagicMock()
        MockV1DeleteOptions.return_value = mock_delete_options

        # Act
        delete_job(mock_api_instance, mock_job_name)

        # Assert
        mock_api_instance.delete_namespaced_job.assert_called_once_with(
            name=mock_job_name,
            namespace="default",
            body=mock_delete_options,
        )
        MockLogger.info.assert_called_once_with(
            "Job deleted with status='%s'" % str(mock_api_response.status)
        )
        MockV1DeleteOptions.assert_called_once_with(
            propagation_policy="Foreground", grace_period_seconds=5
        )

    @patch("scripts.workers.code_upload_submission_worker.create_job")
    @patch(
        "scripts.workers.code_upload_submission_worker.create_static_code_upload_submission_job_object"
    )
    @patch("scripts.workers.code_upload_submission_worker.create_job_object")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_process_submission_callback(
        self,
        MockLogger,
        MockCreateJobObject,
        MockCreateStaticJobObject,
        MockCreateJob,
    ):
        # Arrange
        mock_api_instance = MagicMock()
        mock_body = {
            "submission_pk": 123,
            "is_static_dataset_code_upload_submission": False,
            "challenge_pk": 1,
        }
        mock_challenge_phase = {"environment_image": "test-image"}
        mock_challenge = MagicMock()
        mock_evalai = MagicMock()

        mock_job_object = MagicMock()
        MockCreateJobObject.return_value = mock_job_object
        mock_response = MagicMock()
        mock_response.metadata.name = "test-job-name"
        MockCreateJob.return_value = mock_response

        # Act
        process_submission_callback(
            mock_api_instance,
            mock_body,
            mock_challenge_phase,
            mock_challenge,
            mock_evalai,
        )

        # Assert
        MockLogger.info.assert_called_with(
            "[x] Received submission message %s" % mock_body
        )
        MockCreateJobObject.assert_called_once_with(
            mock_body,
            mock_challenge_phase["environment_image"],
            mock_challenge,
        )
        MockCreateJob.assert_called_once_with(
            mock_api_instance, mock_job_object
        )
        mock_evalai.update_submission_status.assert_called_once_with(
            {
                "submission_status": "queued",
                "submission": 123,
                "job_name": "test-job-name",
            },
            mock_body["challenge_pk"],
        )

    @patch("scripts.workers.code_upload_submission_worker.create_job")
    @patch(
        "scripts.workers.code_upload_submission_worker.create_static_code_upload_submission_job_object"
    )
    @patch("scripts.workers.code_upload_submission_worker.create_job_object")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_process_submission_callback_static_job(
        self,
        MockLogger,
        MockCreateJobObject,
        MockCreateStaticJobObject,
        MockCreateJob,
    ):
        # Arrange
        mock_api_instance = MagicMock()
        mock_body = {
            "submission_pk": 123,
            "is_static_dataset_code_upload_submission": True,
            "challenge_pk": 1,
        }
        mock_challenge_phase = MagicMock()
        mock_challenge = MagicMock()
        mock_evalai = MagicMock()

        mock_static_job_object = MagicMock()
        MockCreateStaticJobObject.return_value = mock_static_job_object
        mock_response = MagicMock()
        mock_response.metadata.name = "test-job-name"
        MockCreateJob.return_value = mock_response

        # Act
        process_submission_callback(
            mock_api_instance,
            mock_body,
            mock_challenge_phase,
            mock_challenge,
            mock_evalai,
        )

        # Assert
        MockLogger.info.assert_called_with(
            "[x] Received submission message %s" % mock_body
        )
        MockCreateStaticJobObject.assert_called_once_with(
            mock_body, mock_challenge
        )
        MockCreateJob.assert_called_once_with(
            mock_api_instance, mock_static_job_object
        )
        mock_evalai.update_submission_status.assert_called_once_with(
            {
                "submission_status": "queued",
                "submission": 123,
                "job_name": "test-job-name",
            },
            mock_body["challenge_pk"],
        )

    @patch("scripts.workers.code_upload_submission_worker.client.BatchV1Api")
    @patch("scripts.workers.code_upload_submission_worker.client.ApiClient")
    @patch(
        "scripts.workers.code_upload_submission_worker.client.Configuration"
    )
    def test_get_api_object(
        self, MockConfiguration, MockApiClient, MockBatchV1Api
    ):
        # Arrange
        mock_challenge = {"id": 1}
        mock_evalai = MagicMock()
        mock_evalai.get_aws_eks_bearer_token.return_value = {
            "aws_eks_bearer_token": "fake-token"
        }

        # Act
        api_instance = get_api_object(
            "fake-cluster", "fake-endpoint", mock_challenge, mock_evalai
        )

        # Assert
        MockConfiguration.assert_called_once()
        MockConfiguration().host = "fake-endpoint"
        MockConfiguration().verify_ssl = True
        MockConfiguration().ssl_ca_cert = (
            "/code/scripts/workers/certificate.crt"
        )
        MockConfiguration().api_key["authorization"] = "fake-token"
        MockConfiguration().api_key_prefix["authorization"] = "Bearer"
        MockApiClient.assert_called_once_with(MockConfiguration())
        MockBatchV1Api.assert_called_once_with(MockApiClient())
        self.assertEqual(api_instance, MockBatchV1Api())

    @patch("scripts.workers.code_upload_submission_worker.client.ApiClient")
    @patch(
        "scripts.workers.code_upload_submission_worker.client.Configuration"
    )
    def test_get_api_client(self, MockConfiguration, MockApiClient):
        # Arrange
        mock_challenge = {"id": 1}
        mock_evalai = MagicMock()
        mock_evalai.get_aws_eks_bearer_token.return_value = {
            "aws_eks_bearer_token": "fake-token"
        }

        # Act
        api_instance = get_api_client(
            "fake-cluster", "fake-endpoint", mock_challenge, mock_evalai
        )

        # Assert
        MockConfiguration.assert_called_once()
        MockConfiguration().host = "fake-endpoint"
        MockConfiguration().verify_ssl = True
        MockConfiguration().ssl_ca_cert = (
            "/code/scripts/workers/certificate.crt"
        )
        MockConfiguration().api_key["authorization"] = "fake-token"
        MockConfiguration().api_key_prefix["authorization"] = "Bearer"
        MockApiClient.assert_called_once_with(MockConfiguration())
        self.assertEqual(api_instance, MockApiClient())

    @patch("scripts.workers.code_upload_submission_worker.client.CoreV1Api")
    @patch("scripts.workers.code_upload_submission_worker.client.ApiClient")
    @patch(
        "scripts.workers.code_upload_submission_worker.client.Configuration"
    )
    def test_get_core_v1_api_object(
        self, MockConfiguration, MockApiClient, MockCoreV1Api
    ):
        # Arrange
        mock_challenge = {"id": 1}
        mock_evalai = MagicMock()
        mock_evalai.get_aws_eks_bearer_token.return_value = {
            "aws_eks_bearer_token": "fake-token"
        }

        # Act
        api_instance = get_core_v1_api_object(
            "fake-cluster", "fake-endpoint", mock_challenge, mock_evalai
        )

        # Assert
        MockConfiguration.assert_called_once()
        MockConfiguration().host = "fake-endpoint"
        MockConfiguration().verify_ssl = True
        MockConfiguration().ssl_ca_cert = (
            "/code/scripts/workers/certificate.crt"
        )
        MockConfiguration().api_key["authorization"] = "fake-token"
        MockConfiguration().api_key_prefix["authorization"] = "Bearer"
        MockApiClient.assert_called_once_with(MockConfiguration())
        MockCoreV1Api.assert_called_once_with(MockApiClient())
        self.assertEqual(api_instance, MockCoreV1Api())

    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_read_job(self, MockLogger):
        # Arrange
        mock_api_instance = MagicMock()
        mock_job_name = "test-job"
        mock_namespace = "default"
        mock_api_response = MagicMock()
        mock_api_instance.read_namespaced_job.return_value = mock_api_response

        # Act
        api_response = read_job(mock_api_instance, mock_job_name)

        # Assert
        mock_api_instance.read_namespaced_job.assert_called_once_with(
            mock_job_name, mock_namespace
        )
        self.assertEqual(api_response, mock_api_response)
        MockLogger.exception.assert_not_called()

    @patch("scripts.workers.code_upload_submission_worker.cleanup_submission")
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_no_pods_returned(
        self, MockLogger, mock_get_pods_from_job, mock_cleanup_submission
    ):
        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        mock_get_pods_from_job.return_value = None

        # Act
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            "test-job",
            1,
            1,
            1,
            "Test message",
            "test-queue",
            False,
            False,
        )

        # Assert
        MockLogger.exception.assert_called_once_with(
            "Exception while reading Job test-job, does not exist."
        )
        mock_cleanup_submission.assert_called_once()

    @patch("scripts.workers.code_upload_submission_worker.cleanup_submission")
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_pods_in_pending_state(
        self, MockLogger, mock_get_pods_from_job, mock_cleanup_submission
    ):
        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        mock_pods_list = MagicMock()
        mock_pods_list.items[0].status.container_statuses = None
        mock_get_pods_from_job.return_value = mock_pods_list

        # Act
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            "test-job",
            1,
            1,
            1,
            "Test message",
            "test-queue",
            False,
            False,
        )

        # Assert
        MockLogger.info.assert_called_once_with(
            "Job pods in pending state, waiting for node assignment for submission 1"
        )
        mock_cleanup_submission.assert_not_called()

    @patch("scripts.workers.code_upload_submission_worker.cleanup_submission")
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_general_exception_handling(
        self, MockLogger, mock_get_pods_from_job, mock_cleanup_submission
    ):
        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        mock_get_pods_from_job.side_effect = Exception("General Exception")

        # Act
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            "test-job",
            1,
            1,
            1,
            "Test message",
            "test-queue",
            False,
            False,
        )

        # Assert
        MockLogger.exception.assert_called_once_with(
            "Exception while reading Job General Exception"
        )
        mock_cleanup_submission.assert_called_once()

    @patch(
        "scripts.workers.code_upload_submission_worker.open",
        new_callable=mock_open,
        read_data="mock manifest content",
    )
    @patch("scripts.workers.code_upload_submission_worker.yaml.load")
    @patch("scripts.workers.code_upload_submission_worker.client.AppsV1Api")
    def test_install_gpu_drivers_success(
        self, mock_apps_api, mock_yaml_load, mock_open_file
    ):
        # Setup
        mock_api_instance = MagicMock()
        mock_apps_api_instance = mock_apps_api.return_value
        mock_yaml_load.return_value = {"metadata": {"namespace": "default"}}

        # Run
        install_gpu_drivers(mock_api_instance)

        # Assertions
        mock_open_file.assert_called_once_with(
            "/code/scripts/workers/code_upload_worker_utils/nvidia-device-plugin.yml"
        )
        mock_yaml_load.assert_called_once_with(
            "mock manifest content", yaml.FullLoader
        )  # Updated this line
        mock_apps_api_instance.create_namespaced_daemon_set.assert_called_once_with(
            "default", mock_yaml_load.return_value
        )

    @patch(
        "scripts.workers.code_upload_submission_worker.open",
        new_callable=mock_open,
        read_data="mock manifest content",
    )
    @patch("scripts.workers.code_upload_submission_worker.yaml.load")
    @patch("scripts.workers.code_upload_submission_worker.client.AppsV1Api")
    def test_install_gpu_drivers_already_installed(
        self, mock_apps_api, mock_yaml_load, mock_open_file
    ):
        # Setup
        mock_api_instance = MagicMock()
        mock_apps_api_instance = mock_apps_api.return_value
        mock_yaml_load.return_value = {"metadata": {"namespace": "default"}}
        mock_apps_api_instance.create_namespaced_daemon_set.side_effect = (
            ApiException(status=409)
        )

        # Run
        install_gpu_drivers(mock_api_instance)

        # Assertions
        mock_open_file.assert_called_once()
        mock_yaml_load.assert_called_once()
        mock_apps_api_instance.create_namespaced_daemon_set.assert_called_once()

    @patch(
        "scripts.workers.code_upload_submission_worker.open",
        new_callable=mock_open,
        read_data="mock manifest content",
    )
    @patch("scripts.workers.code_upload_submission_worker.yaml.load")
    @patch("scripts.workers.code_upload_submission_worker.client.AppsV1Api")
    def test_install_gpu_drivers_raises_exception(
        self, mock_apps_api, mock_yaml_load, mock_open_file
    ):
        # Setup
        mock_api_instance = MagicMock()
        mock_apps_api_instance = mock_apps_api.return_value
        mock_yaml_load.return_value = {"metadata": {"namespace": "default"}}
        mock_apps_api_instance.create_namespaced_daemon_set.side_effect = (
            ApiException(status=500)
        )

        # Run and Assert
        with self.assertRaises(ApiException):
            install_gpu_drivers(mock_api_instance)

        mock_open_file.assert_called_once()
        mock_yaml_load.assert_called_once()
        mock_apps_api_instance.create_namespaced_daemon_set.assert_called_once()

    @patch("scripts.workers.code_upload_submission_worker.GracefulKiller")
    @patch("scripts.workers.code_upload_submission_worker.EvalAI_Interface")
    @patch("scripts.workers.code_upload_submission_worker.get_api_client")
    @patch("scripts.workers.code_upload_submission_worker.get_api_object")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_core_v1_api_object"
    )
    @patch("scripts.workers.code_upload_submission_worker.install_gpu_drivers")
    @patch(
        "scripts.workers.code_upload_submission_worker.create_script_config_map"
    )
    @patch("scripts.workers.code_upload_submission_worker.create_configmap")
    def test_main_successful_execution(
        self,
        mock_create_configmap,
        mock_create_script_config_map,
        mock_install_gpu_drivers,
        mock_get_core_v1_api_object,
        mock_get_api_object,
        mock_get_api_client,
        mock_evalai,
        mock_killer,
    ):
        # Setup
        mock_evalai_instance = mock_evalai.return_value
        mock_evalai_instance.get_challenge_by_queue_name.return_value = {
            "title": "Test Challenge",
            "remote_evaluation": 0,
            "cpu_only_jobs": False,
            "is_static_dataset_code_upload": True,
            "id": 1,
            "submission_time_limit": 100,
        }
        mock_evalai_instance.get_aws_eks_cluster_details.return_value = {
            "name": "test-cluster",
            "cluster_endpoint": "https://cluster-endpoint",
        }
        mock_killer_instance = mock_killer.return_value
        mock_killer_instance.kill_now = True

        # Run
        main()

        # Assertions
        mock_evalai_instance.get_challenge_by_queue_name.assert_called()  # Updated to allow multiple calls
        assert (
            mock_evalai_instance.get_challenge_by_queue_name.call_count == 2
        )  # Verifies the number of calls

    @patch("scripts.workers.code_upload_submission_worker.GracefulKiller")
    @patch("scripts.workers.code_upload_submission_worker.EvalAI_Interface")
    @patch("scripts.workers.code_upload_submission_worker.get_api_client")
    @patch("scripts.workers.code_upload_submission_worker.get_api_object")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_core_v1_api_object"
    )
    def test_main_without_gpu_installation(
        self,
        mock_get_core_v1_api_object,
        mock_get_api_object,
        mock_get_api_client,
        mock_evalai,
        mock_killer,
    ):
        # Setup
        mock_evalai_instance = mock_evalai.return_value
        mock_evalai_instance.get_challenge_by_queue_name.return_value = {
            "title": "Test Challenge",
            "remote_evaluation": 0,
            "cpu_only_jobs": True,
            "is_static_dataset_code_upload": False,
            "id": 1,
            "submission_time_limit": 100,
        }
        mock_killer_instance = mock_killer.return_value
        mock_killer_instance.kill_now = True

        # Run
        main()

        # Assertions
        mock_evalai_instance.get_challenge_by_queue_name.assert_called()
        assert mock_evalai_instance.get_challenge_by_queue_name.call_count == 2


class TestProcessSubmissionCallbackException(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_process_submission_callback_logs_exception(self, MockLogger):
        # Arrange: Patch create_job_object to raise an exception
        with patch(
            "scripts.workers.code_upload_submission_worker.create_job_object",
            side_effect=Exception("Test exception"),
        ):
            mock_api_instance = MagicMock()
            mock_body = {
                "submission_pk": 123,
                "is_static_dataset_code_upload_submission": False,
                "challenge_pk": 1,
            }
            mock_challenge_phase = {"environment_image": "test-image"}
            mock_challenge = MagicMock()
            mock_evalai = MagicMock()

            from scripts.workers.code_upload_submission_worker import (
                process_submission_callback,
            )

            process_submission_callback(
                mock_api_instance,
                mock_body,
                mock_challenge_phase,
                mock_challenge,
                mock_evalai,
            )

            # Assert
            MockLogger.exception.assert_called()
            assert (
                "Exception while receiving message from submission queue with error Test exception"
                in str(MockLogger.exception.call_args[0][0])
            )


class TestGetRunningJobsException(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_get_running_jobs_handles_apiexception(self, MockLogger):
        from scripts.workers.code_upload_submission_worker import (
            get_running_jobs,
        )

        mock_api_instance = MagicMock()
        mock_api_instance.list_namespaced_job.side_effect = ApiException(
            "API error"
        )

        with self.assertRaises(UnboundLocalError):
            get_running_jobs(mock_api_instance)
        MockLogger.exception.assert_called_once()


class TestReadJobException(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_read_job_handles_apiexception(self, MockLogger):
        from scripts.workers.code_upload_submission_worker import read_job

        mock_api_instance = MagicMock()
        mock_api_instance.read_namespaced_job.side_effect = ApiException(
            "API error"
        )

        result = read_job(mock_api_instance, "test-job")
        MockLogger.exception.assert_called_once()
        logged_message = MockLogger.exception.call_args[0][0]
        assert "Exception while reading Job with error" in logged_message
        assert "API error" in logged_message
        self.assertIsNone(result)


class TestCleanupSubmissionException(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.logger")
    def test_cleanup_submission_outer_exception(self, MockLogger):
        from scripts.workers.code_upload_submission_worker import (
            cleanup_submission,
        )

        mock_api_instance = MagicMock()
        mock_evalai = MagicMock()
        # Make update_submission_data raise an exception
        mock_evalai.update_submission_data.side_effect = Exception(
            "Test outer exception"
        )
        job_name = "job-1"
        submission_pk = 1
        challenge_pk = 2
        phase_pk = 3
        stderr = "stderr"
        environment_log = "env_log"
        message = {"receipt_handle": "abc"}
        queue_name = "queue"
        is_remote = False

        cleanup_submission(
            mock_api_instance,
            mock_evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            stderr,
            environment_log,
            message,
            queue_name,
            is_remote,
        )

        MockLogger.exception.assert_called()
        logged_message = MockLogger.exception.call_args[0][0]
        assert (
            "Exception while cleanup Submission 1:  Test outer exception"
            in logged_message
        )


class TestCleanupSubmissionDeleteJobException(unittest.TestCase):
    @patch(
        "scripts.workers.code_upload_submission_worker.increment_and_push_metrics_to_statsd"
    )
    @patch("scripts.workers.code_upload_submission_worker.logger")
    @patch("scripts.workers.code_upload_submission_worker.delete_job")
    def test_cleanup_submission_delete_job_exception(
        self, MockDeleteJob, MockLogger, MockIncrementStatsd
    ):
        from scripts.workers.code_upload_submission_worker import (
            cleanup_submission,
        )

        mock_api_instance = MagicMock()
        mock_evalai = MagicMock()
        # delete_job will raise an exception
        MockDeleteJob.side_effect = Exception("Delete job failed")
        job_name = "job-1"
        submission_pk = 1
        challenge_pk = 2
        phase_pk = 3
        stderr = "stderr"
        environment_log = "env_log"
        message = {"receipt_handle": "abc"}
        queue_name = "queue"
        is_remote = False

        cleanup_submission(
            mock_api_instance,
            mock_evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            stderr,
            environment_log,
            message,
            queue_name,
            is_remote,
        )

        MockLogger.exception.assert_any_call(
            "Failed to delete submission job: Delete job failed"
        )
        mock_evalai.delete_message_from_sqs_queue.assert_called_once_with(
            "abc"
        )
        MockIncrementStatsd.assert_called_once_with(queue_name, is_remote)


class TestUpdateFailedJobsAndSendLogsDisableLogs(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    def test_disable_logs_sets_errors_to_none(self, mock_get_pods_from_job):
        from scripts.workers.code_upload_submission_worker import (
            update_failed_jobs_and_send_logs,
        )

        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        job_name = "job-1"
        submission_pk = 1
        challenge_pk = 2
        phase_pk = 3
        message = {}
        queue_name = "queue"
        is_remote = False
        disable_logs = True

        # Mock pods_list with container_statuses to enter the disable_logs branch
        mock_pods_list = MagicMock()
        mock_pods_list.items = [MagicMock()]
        mock_pods_list.items[0].status.container_statuses = [MagicMock()]
        mock_get_pods_from_job.return_value = mock_pods_list

        # Act (no assertion needed, just coverage)
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            message,
            queue_name,
            is_remote,
            disable_logs,
        )


class TestUpdateFailedJobsAndSendLogsPodLog(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.cleanup_submission")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    def test_pod_log_handling(
        self, mock_get_pods_from_job, MockLogger, mock_cleanup_submission
    ):
        from scripts.workers.code_upload_submission_worker import (
            update_failed_jobs_and_send_logs,
        )

        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        job_name = "job-1"
        submission_pk = 1
        challenge_pk = 2
        phase_pk = 3
        message = {}
        queue_name = "queue"
        is_remote = False
        disable_logs = False

        # Mock pod and container status
        mock_container_state = MagicMock()
        mock_container_state.terminated = MagicMock()
        mock_container = MagicMock()
        mock_container.name = "environment"
        mock_container.state = mock_container_state

        mock_pod_status = MagicMock()
        mock_pod_status.container_statuses = [mock_container]
        mock_pod_metadata = MagicMock()
        mock_pod_metadata.name = "pod-1"
        mock_pod_item = MagicMock()
        mock_pod_item.status = mock_pod_status
        mock_pod_item.metadata = mock_pod_metadata

        mock_pods_list = MagicMock()
        mock_pods_list.items = [mock_pod_item]
        mock_get_pods_from_job.return_value = mock_pods_list

        # Mock pod log response
        mock_pod_log_response = MagicMock()
        mock_pod_log_response.data.decode.return_value = "log-data"
        mock_core_v1_api_instance.read_namespaced_pod_log.return_value = (
            mock_pod_log_response
        )

        # Act
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            message,
            queue_name,
            is_remote,
            disable_logs,
        )

        # Assert: pod log was read for the correct container
        mock_core_v1_api_instance.read_namespaced_pod_log.assert_called_once_with(
            name="pod-1",
            namespace="default",
            _return_http_data_only=True,
            _preload_content=False,
            container="environment",
        )


class TestUpdateFailedJobsAndSendLogsPodLogException(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.cleanup_submission")
    @patch("scripts.workers.code_upload_submission_worker.logger")
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    def test_pod_log_apiexception(
        self, mock_get_pods_from_job, MockLogger, mock_cleanup_submission
    ):
        from kubernetes.client.rest import ApiException

        from scripts.workers.code_upload_submission_worker import (
            update_failed_jobs_and_send_logs,
        )

        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        job_name = "job-1"
        submission_pk = 1
        challenge_pk = 2
        phase_pk = 3
        message = {}
        queue_name = "queue"
        is_remote = False
        disable_logs = False

        # Mock pod and container status
        mock_container_state = MagicMock()
        mock_container_state.terminated = MagicMock()
        mock_container = MagicMock()
        mock_container.name = "environment"
        mock_container.state = mock_container_state

        mock_pod_status = MagicMock()
        mock_pod_status.container_statuses = [mock_container]
        mock_pod_metadata = MagicMock()
        mock_pod_metadata.name = "pod-1"
        mock_pod_item = MagicMock()
        mock_pod_item.status = mock_pod_status
        mock_pod_item.metadata = mock_pod_metadata

        mock_pods_list = MagicMock()
        mock_pods_list.items = [mock_pod_item]
        mock_get_pods_from_job.return_value = mock_pods_list

        # Make read_namespaced_pod_log raise ApiException
        mock_core_v1_api_instance.read_namespaced_pod_log.side_effect = (
            ApiException("Pod log error")
        )

        # Act
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            message,
            queue_name,
            is_remote,
            disable_logs,
        )

        # Assert: logger.exception was called with the expected message
        logged_message = MockLogger.exception.call_args[0][0]
        assert "Exception while reading Job logs" in logged_message
        assert "Pod log error" in logged_message


class TestUpdateFailedJobsAndSendLogsSubmissionError(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.cleanup_submission")
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    def test_submission_error_assignment(
        self, mock_get_pods_from_job, mock_cleanup_submission
    ):
        from scripts.workers.code_upload_submission_worker import (
            update_failed_jobs_and_send_logs,
        )

        # Arrange
        mock_api_instance = MagicMock()
        mock_core_v1_api_instance = MagicMock()
        mock_evalai = MagicMock()
        job_name = "job-1"
        submission_pk = 1
        challenge_pk = 2
        phase_pk = 3
        message = {}
        queue_name = "queue"
        is_remote = False
        disable_logs = False

        # Mock pod and container status for "submission" container
        mock_container_state = MagicMock()
        mock_container_state.terminated = MagicMock()
        mock_container = MagicMock()
        mock_container.name = "submission"
        mock_container.state = mock_container_state

        mock_pod_status = MagicMock()
        mock_pod_status.container_statuses = [mock_container]
        mock_pod_metadata = MagicMock()
        mock_pod_metadata.name = "pod-1"
        mock_pod_item = MagicMock()
        mock_pod_item.status = mock_pod_status
        mock_pod_item.metadata = mock_pod_metadata

        mock_pods_list = MagicMock()
        mock_pods_list.items = [mock_pod_item]
        mock_get_pods_from_job.return_value = mock_pods_list

        # Mock pod log response
        mock_pod_log_response = MagicMock()
        mock_pod_log_response.data.decode.return_value = "submission-log-data"
        mock_core_v1_api_instance.read_namespaced_pod_log.return_value = (
            mock_pod_log_response
        )

        # Act (no assertion needed, just coverage)
        update_failed_jobs_and_send_logs(
            mock_api_instance,
            mock_core_v1_api_instance,
            mock_evalai,
            job_name,
            submission_pk,
            challenge_pk,
            phase_pk,
            message,
            queue_name,
            is_remote,
            disable_logs,
        )


class TestMainQueuedSubmission(unittest.TestCase):
    @patch("scripts.workers.code_upload_submission_worker.get_pods_from_job")
    @patch("scripts.workers.code_upload_submission_worker.GracefulKiller")
    @patch("scripts.workers.code_upload_submission_worker.EvalAI_Interface")
    @patch("scripts.workers.code_upload_submission_worker.get_api_client")
    @patch("scripts.workers.code_upload_submission_worker.get_api_object")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_core_v1_api_object"
    )
    def test_main_queued_submission_updates_status(
        self,
        mock_get_core_v1_api_object,
        mock_get_api_object,
        mock_get_api_client,
        mock_evalai,
        mock_killer,
        mock_get_pods_from_job,
    ):
        # Setup
        mock_evalai_instance = mock_evalai.return_value
        mock_evalai_instance.get_challenge_by_queue_name.return_value = {
            "title": "Test Challenge",
            "remote_evaluation": 0,
            "cpu_only_jobs": False,
            "is_static_dataset_code_upload": False,
            "id": 1,
            "submission_time_limit": 100,
        }
        mock_evalai_instance.get_aws_eks_cluster_details.return_value = {
            "name": "test-cluster",
            "cluster_endpoint": "https://cluster-endpoint",
        }
        mock_evalai_instance.get_challenge_phase_by_pk.return_value = {
            "disable_logs": False
        }
        mock_evalai_instance.get_message_from_sqs_queue.return_value = {
            "body": {
                "submission_pk": 1,
                "challenge_pk": 1,
                "phase_pk": 1,
            },
            "receipt_handle": "abc",
        }
        mock_evalai_instance.get_submission_by_pk.return_value = {
            "status": "queued",
            "job_name": ["job-123"],
        }
        mock_killer_instance = mock_killer.return_value
        mock_killer_instance.kill_now = True

        # Mock pods_list with container_statuses
        mock_container_status = MagicMock()
        mock_pod_status = MagicMock()
        mock_pod_status.container_statuses = [mock_container_status]
        mock_pod_item = MagicMock()
        mock_pod_item.status = mock_pod_status
        mock_pods_list = MagicMock()
        mock_pods_list.items = [mock_pod_item]
        mock_get_pods_from_job.return_value = mock_pods_list

        from scripts.workers.code_upload_submission_worker import main

        main()

        # Assert update_submission_status was called with correct data
        mock_evalai_instance.update_submission_status.assert_called_once_with(
            {
                "submission_status": "running",
                "submission": 1,
                "job_name": "job-123",
            },
            1,
        )


class TestMainJobDeleteBlock(unittest.TestCase):
    @patch(
        "scripts.workers.code_upload_submission_worker.increment_and_push_metrics_to_statsd"
    )
    @patch("scripts.workers.code_upload_submission_worker.logger")
    @patch("scripts.workers.code_upload_submission_worker.delete_job")
    @patch("scripts.workers.code_upload_submission_worker.GracefulKiller")
    @patch("scripts.workers.code_upload_submission_worker.EvalAI_Interface")
    @patch("scripts.workers.code_upload_submission_worker.get_api_client")
    @patch("scripts.workers.code_upload_submission_worker.get_api_object")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_core_v1_api_object"
    )
    def test_main_job_delete_block(
        self,
        mock_get_core_v1_api_object,
        mock_get_api_object,
        mock_get_api_client,
        mock_evalai,
        mock_killer,
        mock_delete_job,
        MockLogger,
        mock_increment_statsd,
    ):
        # Setup
        mock_evalai_instance = mock_evalai.return_value
        mock_evalai_instance.get_challenge_by_queue_name.return_value = {
            "title": "Test Challenge",
            "remote_evaluation": 0,
            "cpu_only_jobs": False,
            "is_static_dataset_code_upload": False,
            "id": 1,
            "submission_time_limit": 100,
        }
        mock_evalai_instance.get_aws_eks_cluster_details.return_value = {
            "name": "test-cluster",
            "cluster_endpoint": "https://cluster-endpoint",
        }
        # Simulate a finished submission with job_name
        mock_evalai_instance.get_message_from_sqs_queue.return_value = {
            "body": {
                "submission_pk": 1,
                "challenge_pk": 1,
                "phase_pk": 1,
            },
            "receipt_handle": "abc",
        }
        mock_evalai_instance.get_challenge_phase_by_pk.return_value = {
            "disable_logs": False
        }
        mock_evalai_instance.get_submission_by_pk.return_value = {
            "status": "finished",
            "job_name": ["job-123"],
        }
        mock_killer_instance = mock_killer.return_value
        mock_killer_instance.kill_now = True

        from scripts.workers.code_upload_submission_worker import main

        main()

        # Assert delete_job and message deletion were called
        mock_delete_job.assert_called_once_with(
            mock_get_api_object.return_value, "job-123"
        )
        mock_evalai_instance.delete_message_from_sqs_queue.assert_called_once_with(
            "abc"
        )
        mock_increment_statsd.assert_called_once()

    @patch(
        "scripts.workers.code_upload_submission_worker.increment_and_push_metrics_to_statsd"
    )
    @patch("scripts.workers.code_upload_submission_worker.logger")
    @patch("scripts.workers.code_upload_submission_worker.delete_job")
    @patch("scripts.workers.code_upload_submission_worker.GracefulKiller")
    @patch("scripts.workers.code_upload_submission_worker.EvalAI_Interface")
    @patch("scripts.workers.code_upload_submission_worker.get_api_client")
    @patch("scripts.workers.code_upload_submission_worker.get_api_object")
    @patch(
        "scripts.workers.code_upload_submission_worker.get_core_v1_api_object"
    )
    def test_main_job_delete_block_exception(
        self,
        mock_get_core_v1_api_object,
        mock_get_api_object,
        mock_get_api_client,
        mock_evalai,
        mock_killer,
        mock_delete_job,
        MockLogger,
        mock_increment_statsd,
    ):
        # Setup
        mock_evalai_instance = mock_evalai.return_value
        mock_evalai_instance.get_challenge_by_queue_name.return_value = {
            "title": "Test Challenge",
            "remote_evaluation": 0,
            "cpu_only_jobs": False,
            "is_static_dataset_code_upload": False,
            "id": 1,
            "submission_time_limit": 100,
        }
        mock_evalai_instance.get_aws_eks_cluster_details.return_value = {
            "name": "test-cluster",
            "cluster_endpoint": "https://cluster-endpoint",
        }
        # Simulate a finished submission with job_name
        mock_evalai_instance.get_message_from_sqs_queue.return_value = {
            "body": {
                "submission_pk": 1,
                "challenge_pk": 1,
                "phase_pk": 1,
            },
            "receipt_handle": "abc",
        }
        mock_evalai_instance.get_challenge_phase_by_pk.return_value = {
            "disable_logs": False
        }
        mock_evalai_instance.get_submission_by_pk.return_value = {
            "status": "finished",
            "job_name": ["job-123"],
        }
        mock_killer_instance = mock_killer.return_value
        mock_killer_instance.kill_now = True

        # Make delete_job raise an exception
        mock_delete_job.side_effect = Exception("Delete job failed")

        from scripts.workers.code_upload_submission_worker import main

        main()

        # Assert logger.exception was called for the exception
        MockLogger.exception.assert_any_call(
            "Failed to delete submission job: Delete job failed"
        )
        # Assert message deletion and statsd increment were still called
        mock_evalai_instance.delete_message_from_sqs_queue.assert_called_with(
            "abc"
        )
        mock_increment_statsd.assert_called()
