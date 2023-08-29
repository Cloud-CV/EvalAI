import mock
from rest_framework.test import APITestCase
import os

from scripts.workers.code_upload_submission_worker import (
    get_volume_mount_object,
    get_volume_mount_list,
    get_volume_list,
    get_empty_volume_object,
    get_config_map_volume_object,
    create_config_map_object,
    create_configmap,
    create_script_config_map,
    get_submission_meta_update_curl,
    get_job_object,
    get_init_container,
    get_job_constraints,
    create_job_object,
    create_static_code_upload_submission_job_object,
    create_job,
    delete_job,
    process_submission_callback,
    get_api_object,
    get_api_client,
    get_core_v1_api_object,
    get_running_jobs,
    read_job,
    cleanup_submission,
    update_failed_jobs_and_send_logs,
    install_gpu_drivers,
)


class BaseAPITestClass(APITestCase):
    def test_get_volume_mount_object(self):
        mount_path = "/evalai_scripts"
        name = "evalai-scripts"
        read_only = False
        volume_mount = get_volume_mount_object(mount_path, name, read_only)
        self.assertEqual(volume_mount.mount_path, mount_path)
        self.assertEqual(volume_mount.name, name)
        self.assertEqual(volume_mount.read_only, read_only)

    def test_get_volume_mount_list(self):
        mount_path = "/path/to/mount"
        read_only = False
        volume_mount_list = get_volume_mount_list(mount_path, read_only)
        self.assertEqual(len(volume_mount_list), 1)
        self.assertEqual(volume_mount_list[0].mount_path, mount_path)
        self.assertEqual(volume_mount_list[0].read_only, read_only)

    def test_get_volume_list(self):
        volume_list = get_volume_list()
        self.assertEqual(len(volume_list), 1)
        self.assertEqual(volume_list[0].name, "efs-claim")
        self.assertEqual(
            volume_list[0].persistent_volume_claim.claim_name, "efs-claim"
        )

    def test_get_empty_volume_object(self):
        volume_name = "volume_name"
        volume = get_empty_volume_object(volume_name)
        self.assertEqual(volume.name, volume_name)
        self.assertTrue(volume.empty_dir is not None)

    def test_get_config_map_volume_object(self):
        config_map_name = "config_map_name"
        volume_name = "volume_name"
        volume = get_config_map_volume_object(config_map_name, volume_name)
        self.assertEqual(volume.name, volume_name)
        self.assertEqual(volume.config_map.name, config_map_name)

    def test_create_config_map_object(self):
        config_map_name = "config_map_name"
        file_paths = [
            "/code/scripts/workers/code_upload_worker_utils/make_submission.sh",
            "/code/scripts/workers/code_upload_worker_utils/monitor_submission.sh",
        ]
        config_map = create_config_map_object(config_map_name, file_paths)
        self.assertEqual(config_map.metadata.name, config_map_name)
        self.assertEqual(len(config_map.data), len(file_paths))
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            self.assertIn(file_name, config_map.data)
            file_content = open(file_path, "r").read()
            self.assertEqual(config_map.data[file_name], file_content)

    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_core_v1_api_object"
    )
    def test_create_configmap(self, mock_get_core_v1_api_object):
        config_map = mock.MagicMock()
        mock_list_namespaced_config_map = mock.MagicMock()
        mock_list_namespaced_config_map.items = []
        mock_get_core_v1_api_object.list_namespaced_config_map.return_value = (
            mock_list_namespaced_config_map
        )

        create_configmap(mock_get_core_v1_api_object, config_map)

        mock_get_core_v1_api_object.list_namespaced_config_map.assert_called_once_with(
            namespace="default"
        )
        mock_get_core_v1_api_object.create_namespaced_config_map.assert_called_once_with(
            namespace="default", body=config_map
        )

    def test_create_script_config_map(self):
        config_map_name = "evalai-scripts-cm"
        script_config_map = create_script_config_map(config_map_name)
        self.assertEqual(script_config_map.metadata.name, config_map_name)
        self.assertEqual(len(script_config_map.data), 2)
        self.assertIn("make_submission.sh", script_config_map.data)
        self.assertIn("monitor_submission.sh", script_config_map.data)

    def test_get_submission_meta_update_curl(self):
        submission_pk = 12345
        expected_url = "http://localhost:8000/api/jobs/submission/12345/update_started_at/"
        expected_curl_request = "curl --location --request PATCH '{}' --header 'Authorization: Bearer auth_token'".format(
            expected_url
        )
        curl_request = get_submission_meta_update_curl(submission_pk)
        self.assertEqual(curl_request, expected_curl_request)

    def test_get_job_object(self):
        submission_pk = 12345
        spec = mock.MagicMock()
        job = get_job_object(submission_pk, spec)
        self.assertEqual(job.api_version, "batch/v1")
        self.assertEqual(job.kind, "Job")
        self.assertEqual(job.metadata.name, "submission-12345")
        self.assertEqual(job.spec, spec)

    def test_get_init_container(self):
        submission_pk = 12345
        curl_request = "curl-request"
        mock_get_submission_meta_update_curl = mock.patch(
            "scripts.workers.code_upload_submission_worker.get_submission_meta_update_curl"
        ).start()
        mock_get_submission_meta_update_curl.return_value = curl_request

        init_container = get_init_container(submission_pk)

        self.assertEqual(init_container.name, "init-container")
        self.assertEqual(init_container.image, "ubuntu")
        self.assertEqual(
            init_container.command,
            [
                "/bin/bash",
                "-c",
                "apt update && apt install -y curl && {}".format(curl_request),
            ],
        )

        mock_get_submission_meta_update_curl.assert_called_once_with(
            submission_pk
        )
        mock_get_submission_meta_update_curl.stop()

    def test_get_job_constraints_with_gpu(self):
        challenge = {
            "cpu_only_jobs": False,
            "job_cpu_cores": None,
            "job_memory": None,
        }
        constraints = get_job_constraints(challenge)
        self.assertEqual(constraints["nvidia.com/gpu"], "1")

    def test_get_job_constraints_without_gpu(self):
        challenge = {
            "cpu_only_jobs": True,
            "job_cpu_cores": "2",
            "job_memory": "4Gi",
        }
        constraints = get_job_constraints(challenge)
        self.assertEqual(constraints["cpu"], "2")
        self.assertEqual(constraints["memory"], "4Gi")

    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_submission_meta_update_curl"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_volume_mount_list"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_volume_list"
    )
    def test_create_job_object(
        self,
        mock_get_volume_list,
        mock_get_volume_mount_list,
        mock_get_submission_meta_update_curl,
    ):
        message = {
            "submission_pk": 12345,
            "submitted_image_uri": "image_uri",
            "submission_meta": {"submission_time_limit": 100},
        }
        environment_image = "environment_image"
        challenge = {
            "cpu_only_jobs": False,
            "job_cpu_cores": None,
            "job_memory": None,
        }
        mock_get_submission_meta_update_curl.return_value = "curl-request"
        mock_get_volume_list.return_value = ["volume"]
        mock_get_volume_mount_list.return_value = ["volume_mount"]

        job = create_job_object(message, environment_image, challenge)

        self.assertEqual(job.metadata.name, "submission-12345")
        self.assertEqual(len(job.spec.template.spec.init_containers), 1)
        self.assertEqual(
            job.spec.template.spec.init_containers[0].name, "init-container"
        )
        self.assertEqual(
            job.spec.template.spec.init_containers[0].image, "ubuntu"
        )
        self.assertEqual(
            job.spec.template.spec.containers[1].name, "agent"
        )  # Assuming agent container is the second container
        self.assertEqual(
            job.spec.template.spec.containers[1].image, "image_uri"
        )  # Assuming agent container is the second container
        self.assertEqual(
            job.spec.template.spec.containers[1].env[0].name,
            "PYTHONUNBUFFERED",
        )
        self.assertEqual(
            job.spec.template.spec.containers[1].env[0].value, "1"
        )
        self.assertEqual(
            job.spec.template.spec.volumes,
            ["volume"],
        )

        mock_get_submission_meta_update_curl.assert_called_once_with(12345)
        mock_get_volume_list.assert_called_once()
        mock_get_volume_mount_list.assert_called_once_with("/dataset")

        mock_get_submission_meta_update_curl.stop()
        mock_get_volume_list.stop()
        mock_get_volume_mount_list.stop()

    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_job_constraints"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_init_container"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_volume_mount_list"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_volume_list"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_config_map_volume_object"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_volume_mount_object"
    )
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.get_empty_volume_object"
    )
    @mock.patch("scripts.workers.code_upload_submission_worker.get_job_object")
    def test_create_static_code_upload_submission_job_object(
        self,
        mock_get_job_object,
        mock_get_empty_volume_object,
        mock_get_volume_mount_object,
        mock_get_config_map_volume_object,
        mock_get_volume_list,
        mock_get_volume_mount_list,
        mock_get_init_container,
        mock_get_job_constraints,
    ):
        # Define the mock return values
        submission_pk = 12345
        challenge_pk = 54321
        phase_pk = 98765
        submission_meta = {"submission_time_limit": 100}
        message = {
            "submission_pk": submission_pk,
            "challenge_pk": challenge_pk,
            "phase_pk": phase_pk,
            "submission_meta": submission_meta,
            "submitted_image_uri": "image_uri",
        }
        challenge = {
            "cpu_only_jobs": False,
            "job_cpu_cores": None,
            "job_memory": None,
        }
        get_job_constraints_result = {"limits": {"cpu": "1", "memory": "1Gi"}}
        init_container = mock.MagicMock()
        volume_mount_list = mock.MagicMock()
        volume_list = mock.MagicMock()
        script_volume = mock.MagicMock()
        submission_volume_name = "submissions-dir"
        submission_volume = mock.MagicMock()
        # Call the function to create the job object
        job = create_static_code_upload_submission_job_object(
            message, challenge
        )
        # Configure the mock objects
        mock_get_job_constraints.return_value = get_job_constraints_result
        mock_get_empty_volume_object.return_value = submission_volume
        mock_get_volume_mount_object.return_value = mock.MagicMock()
        mock_get_config_map_volume_object.return_value = script_volume
        mock_get_volume_list.return_value = volume_list
        mock_get_volume_mount_list.return_value = volume_mount_list
        mock_get_init_container.return_value = init_container
        mock_get_job_object.return_value = job

        # Assert the expected values
        self.assertEqual(job, mock_get_job_object.return_value)
        mock_get_job_constraints.assert_called_once_with(challenge)
        mock_get_empty_volume_object.assert_called_once_with(
            submission_volume_name
        )
        mock_get_volume_mount_object.assert_called_with(
            "/submission", submission_volume_name
        )
        mock_get_volume_list.assert_called_once()
        mock_get_volume_mount_list.assert_called_once_with("/dataset", True)
        mock_get_init_container.assert_called_once_with(submission_pk)

    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_create_job(self, mock_client):
        api_instance = mock_client.BatchV1Api.return_value
        job = mock.MagicMock()
        api_response = mock.MagicMock()
        api_instance.create_namespaced_job.return_value = api_response

        result = create_job(api_instance, job)

        self.assertEqual(result, api_response)
        api_instance.create_namespaced_job.assert_called_once_with(
            body=job, namespace="default", pretty=True
        )

    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_delete_job(self, mock_client):
        api_instance = mock_client.BatchV1Api.return_value
        job_name = "submission-12345"
        api_response = mock.MagicMock()
        api_instance.delete_namespaced_job.return_value = api_response

        delete_job(api_instance, job_name)

        api_instance.delete_namespaced_job.assert_called_once_with(
            name=job_name,
            namespace="default",
            body=mock_client.V1DeleteOptions(
                propagation_policy="Foreground", grace_period_seconds=5
            ),
        )

    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.create_static_code_upload_submission_job_object"
    )
    @mock.patch("scripts.workers.code_upload_submission_worker.create_job")
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.create_job_object"
    )
    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_process_submission_callback_static(
        self,
        mock_client,
        mock_create_job_object,
        mock_create_job,
        mock_create_static_code_upload_submission_job_object,
        mock_logger,
    ):
        api_instance = mock_client.BatchV1Api.return_value
        body = {
            "is_static_dataset_code_upload_submission": True,
            "submission_pk": 12345,
            "challenge_pk": 67890,
            "phase_pk": 54321,
            "submitted_image_uri": "image_uri",
            "submission_meta": {"submission_time_limit": 86400},
        }
        challenge = {"id": 67890}
        evalai = mock.MagicMock()
        job = mock.MagicMock()
        response = mock.MagicMock()
        api_instance.create_namespaced_job.return_value = response

        mock_create_static_code_upload_submission_job_object.return_value = job

        process_submission_callback(
            api_instance, body, None, challenge, evalai
        )

        mock_logger.info.assert_called_once_with(
            "[x] Received submission message %s" % body
        )
        mock_create_static_code_upload_submission_job_object.assert_called_once_with(
            body, challenge
        )

    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.create_static_code_upload_submission_job_object"
    )
    @mock.patch("scripts.workers.code_upload_submission_worker.create_job")
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.create_job_object"
    )
    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_process_submission_callback_non_static(
        self,
        mock_client,
        mock_create_job_object,
        mock_create_job,
        mock_create_static_code_upload_submission_job_object,
        mock_logger,
    ):
        api_instance = mock_client.BatchV1Api.return_value
        body = {
            "is_static_dataset_code_upload_submission": False,
            "submission_pk": 12345,
            "challenge_pk": 67890,
            "phase_pk": 54321,
            "submitted_image_uri": "image_uri",
            "submission_meta": {"submission_time_limit": 86400},
        }
        challenge = {"id": 67890}
        evalai = mock.MagicMock()
        job = mock.MagicMock()
        response = mock.MagicMock()
        api_instance.create_namespaced_job.return_value = response

        mock_create_job_object.return_value = job

        process_submission_callback(
            api_instance, body, None, challenge, evalai
        )

        mock_logger.info.assert_called_once_with(
            "[x] Received submission message %s" % body
        )
        mock_create_static_code_upload_submission_job_object.assert_not_called()

    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_get_api_object(self, mock_client):
        cluster_name = "cluster_name"
        cluster_endpoint = "cluster_endpoint"
        challenge = {"id": 12345}
        evalai = mock.MagicMock()
        api_instance = mock_client.BatchV1Api.return_value

        result = get_api_object(
            cluster_name, cluster_endpoint, challenge, evalai
        )

        self.assertEqual(result, api_instance)
        mock_client.Configuration.assert_called_once()
        evalai.get_aws_eks_bearer_token.assert_called_once_with(12345)
        mock_client.ApiClient.assert_called_once_with(
            mock_client.Configuration.return_value
        )
        mock_client.BatchV1Api.assert_called_once()

    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_get_api_client(self, mock_client):
        cluster_name = "cluster_name"
        cluster_endpoint = "cluster_endpoint"
        challenge = {"id": 12345}
        evalai = mock.MagicMock()
        api_instance = mock_client.ApiClient.return_value

        result = get_api_client(
            cluster_name, cluster_endpoint, challenge, evalai
        )

        self.assertEqual(result, api_instance)
        mock_client.Configuration.assert_called_once()
        evalai.get_aws_eks_bearer_token.assert_called_once_with(12345)
        mock_client.ApiClient.assert_called_once_with(
            mock_client.Configuration.return_value
        )

    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_get_core_v1_api_object(self, mock_client):
        cluster_name = "cluster_name"
        cluster_endpoint = "cluster_endpoint"
        challenge = {"id": 12345}
        evalai = mock.MagicMock()
        api_instance = mock_client.CoreV1Api.return_value

        result = get_core_v1_api_object(
            cluster_name, cluster_endpoint, challenge, evalai
        )

        self.assertEqual(result, api_instance)
        mock_client.Configuration.assert_called_once()
        evalai.get_aws_eks_bearer_token.assert_called_once_with(12345)
        mock_client.ApiClient.assert_called_once_with(
            mock_client.Configuration.return_value
        )
        mock_client.CoreV1Api.assert_called_once()

    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_get_running_jobs(self, mock_client, mock_logger):
        api_instance = mock_client.BatchV1Api.return_value
        api_response = mock.MagicMock()
        api_instance.list_namespaced_job.return_value = api_response

        result = get_running_jobs(api_instance)

        self.assertEqual(result, api_response)
        api_instance.list_namespaced_job.assert_called_once_with("default")
        mock_logger.exception.assert_not_called()

    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    def test_read_job(self, mock_client, mock_logger):
        api_instance = mock_client.BatchV1Api.return_value
        api_response = mock.MagicMock()
        api_instance.read_namespaced_job.return_value = api_response

        result = read_job(api_instance, "job_name")

        self.assertEqual(result, api_response)
        api_instance.read_namespaced_job.assert_called_once_with(
            "job_name", "default"
        )
        mock_logger.exception.assert_not_called()

    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch("scripts.workers.code_upload_submission_worker.delete_job")
    def test_cleanup_submission(self, mock_delete_job, mock_logger):
        api_instance = mock.MagicMock()
        evalai = mock.MagicMock()
        job_name = "job_name"
        submission_pk = 12345
        challenge_pk = 67890
        phase_pk = 54321
        stderr = "error"
        environment_log = "environment_log"
        message = {"receipt_handle": "receipt_handle"}
        queue_name = "queue_name"
        is_remote = 1

        cleanup_submission(
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
        )

        evalai.update_submission_data.assert_called_once_with(
            {
                "challenge_phase": 54321,
                "submission": 12345,
                "stdout": "",
                "stderr": "error",
                "environment_log": "environment_log",
                "submission_status": "FAILED",
                "result": "[]",
                "metadata": "",
            },
            67890,
            54321,
        )
        mock_delete_job.assert_called_once_with(api_instance, "job_name")
        evalai.delete_message_from_sqs_queue.assert_called_once_with(
            "receipt_handle"
        )
        mock_logger.exception.assert_not_called()

    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch("scripts.workers.code_upload_submission_worker.delete_job")
    def test_cleanup_submission_delete_job_exception(
        self, mock_delete_job, mock_logger
    ):
        api_instance = mock.MagicMock()
        evalai = mock.MagicMock()
        job_name = "job_name"
        submission_pk = 12345
        challenge_pk = 67890
        phase_pk = 54321
        stderr = "error"
        environment_log = "environment_log"
        message = {"receipt_handle": "receipt_handle"}
        queue_name = "queue_name"
        is_remote = 1

        mock_delete_job.side_effect = Exception("Some error")

        cleanup_submission(
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
        )

        evalai.update_submission_data.assert_called_once_with(
            {
                "challenge_phase": 54321,
                "submission": 12345,
                "stdout": "",
                "stderr": "error",
                "environment_log": "environment_log",
                "submission_status": "FAILED",
                "result": "[]",
                "metadata": "",
            },
            67890,
            54321,
        )
        mock_delete_job.assert_called_once_with(api_instance, "job_name")
        evalai.delete_message_from_sqs_queue.assert_called_once_with(
            "receipt_handle"
        )
        mock_logger.exception.assert_called_once_with(
            "Failed to delete submission job: {}".format("Some error")
        )

    @mock.patch("scripts.workers.code_upload_submission_worker.read_job")
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.cleanup_submission"
    )
    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    @mock.patch("scripts.workers.code_upload_submission_worker.GracefulKiller")
    @mock.patch(
        "scripts.workers.code_upload_submission_worker.EvalAI_Interface"
    )
    def test_update_failed_jobs_and_send_logs(
        self,
        mock_evalai_interface,
        mock_graceful_killer,
        mock_client,
        mock_logger,
        mock_cleanup_submission,
        mock_read_job,
    ):
        api_instance = mock_client.BatchV1Api.return_value
        core_v1_api_instance = mock_client.CoreV1Api.return_value
        evalai = mock_evalai_interface.return_value
        job_name = "job_name"
        submission_pk = 12345
        challenge_pk = 67890
        phase_pk = 54321
        message = {"receipt_handle": "receipt_handle"}
        queue_name = "queue_name"
        is_remote = 1
        disable_logs = False

        job_def = mock.MagicMock()
        job_def.metadata.labels = {"controller-uid": "controller_uid"}
        mock_read_job.return_value = job_def

        pods_list = mock.MagicMock()
        pods_list.items = [
            mock.MagicMock(
                status=mock.MagicMock(
                    container_statuses=[
                        mock.MagicMock(
                            name="agent",
                            state=mock.MagicMock(terminated=None),
                        ),
                        mock.MagicMock(
                            name="submission",
                            state=mock.MagicMock(terminated=mock.MagicMock()),
                        ),
                        mock.MagicMock(
                            name="environment",
                            state=mock.MagicMock(terminated=mock.MagicMock()),
                        ),
                    ]
                ),
                metadata=mock.MagicMock(name="pod_name"),
            )
        ]
        core_v1_api_instance.list_namespaced_pod.return_value = pods_list

        pod_log_response = mock.MagicMock()
        pod_log_response.data.decode.return_value = "pod_log"
        core_v1_api_instance.read_namespaced_pod_log.return_value = (
            pod_log_response
        )

        update_failed_jobs_and_send_logs(
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
            disable_logs,
        )

        mock_read_job.assert_called_once_with(api_instance, job_name)
        core_v1_api_instance.list_namespaced_pod.assert_called_once_with(
            namespace="default",
            label_selector="controller-uid=controller_uid",
            timeout_seconds=10,
        )

    @mock.patch("scripts.workers.code_upload_submission_worker.open")
    @mock.patch("scripts.workers.code_upload_submission_worker.logger")
    @mock.patch("scripts.workers.code_upload_submission_worker.client")
    @mock.patch("scripts.workers.code_upload_submission_worker.yaml")
    def test_install_gpu_drivers(
        self, mock_yaml, mock_client, mock_logger, mock_open
    ):
        api_instance = mock_client.AppsV1Api.return_value

        mock_open.return_value.read.return_value = "nvidia_manifest"

        install_gpu_drivers(api_instance)

        mock_open.assert_called_once_with(
            "/code/scripts/workers/code_upload_worker_utils/nvidia-device-plugin.yml"
        )
        mock_yaml.load.assert_called_once_with(
            "nvidia_manifest", mock_yaml.FullLoader
        )
