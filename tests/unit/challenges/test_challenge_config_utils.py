import io
import os
import tempfile
import unittest
import uuid
import zipfile
from datetime import timedelta
from os.path import basename, join
from unittest.mock import Mock
from unittest.mock import patch as mockpatch

import pytest
import requests
import yaml
from challenges.challenge_config_utils import (
    ValidateChallengeConfigUtil,
    download_and_write_file,
    error_message_dict,
    get_value_from_field,
    get_yaml_files_from_challenge_config,
    get_yaml_read_error,
    is_challenge_config_yaml_html_field_valid,
    is_challenge_phase_config_yaml_html_field_valid,
    is_challenge_phase_split_mapping_valid,
    read_yaml_file,
    validate_challenge_config_util,
)
from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
)
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from hosts.models import ChallengeHostTeam


class TestGetYamlFilesFromChallengeConfig(unittest.TestCase):
    def test_no_yaml_files_in_zip(self):
        # Create a zip file in memory with no YAML files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "a", zipfile.ZIP_DEFLATED
        ) as zip_file:
            zip_file.writestr(
                "some_other_file.txt", "This is some other file content"
            )

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            (
                yaml_file_count,
                yaml_file_name,
                extracted_folder_name,
            ) = get_yaml_files_from_challenge_config(zip_file)

        self.assertEqual(yaml_file_count, 0)
        self.assertIsNone(yaml_file_name)
        self.assertIsNone(extracted_folder_name)


class TestGetYamlReadError(unittest.TestCase):
    def test_get_yaml_read_error_with_problem_and_problem_mark(self):
        # Create a mock exception with problem and problem_mark attributes
        class MockException:
            def __init__(self, problem, line, column):
                self.problem = problem
                self.problem_mark = self.Mark(line, column)

            class Mark:
                def __init__(self, line, column):
                    self.line = line
                    self.column = column

        exc = MockException("mock problem", 10, 20)
        error_description, line_number, column_number = get_yaml_read_error(
            exc
        )

        self.assertEqual(error_description, "Mock problem")
        self.assertEqual(line_number, 11)
        self.assertEqual(column_number, 21)

    def test_get_yaml_read_error_without_problem_and_problem_mark(self):
        # Create a mock exception without problem and problem_mark attributes
        class MockException:
            pass

        exc = MockException()
        error_description, line_number, column_number = get_yaml_read_error(
            exc
        )

        self.assertIsNone(error_description)
        self.assertIsNone(line_number)
        self.assertIsNone(column_number)


class TestIsChallengeConfigYamlHtmlFieldValid(unittest.TestCase):
    def setUp(self):
        self.base_location = "/path/to/extracted/config"

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=False)
    def test_file_not_found(self, mock_isfile):
        yaml_file_data = {"html_field": "non_existent_file.html"}
        key = "html_field"

        is_valid, message = is_challenge_config_yaml_html_field_valid(
            yaml_file_data, key, self.base_location
        )

        self.assertFalse(is_valid)
        self.assertEqual(
            message,
            "File at path html_field not found. Please specify a valid file path",
        )

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=True)
    def test_file_not_html(self, mock_isfile):
        yaml_file_data = {"html_field": "file.txt"}
        key = "html_field"

        is_valid, message = is_challenge_config_yaml_html_field_valid(
            yaml_file_data, key, self.base_location
        )

        self.assertFalse(is_valid)
        self.assertEqual(
            message,
            "File html_field is not a HTML file. Please specify a valid HTML file",
        )


class TestIsChallengePhaseSplitMappingValid(unittest.TestCase):
    def test_invalid_dataset_split_id(self):
        phase_ids = [1, 2, 3]
        leaderboard_ids = [10, 20, 30]
        dataset_split_ids = [100, 200, 300]
        phase_split = {
            "challenge_phase_id": 1,
            "leaderboard_id": 10,
            "dataset_split_id": 400,  # Invalid dataset split id
        }
        challenge_phase_split_index = 0

        is_success, error_messages = is_challenge_phase_split_mapping_valid(
            phase_ids,
            leaderboard_ids,
            dataset_split_ids,
            phase_split,
            challenge_phase_split_index,
        )

        self.assertFalse(is_success)
        self.assertIn(
            "ERROR: Invalid dataset split id 400 found in challenge phase split 0.",
            error_messages,
        )


class TestDownloadAndWriteFile(unittest.TestCase):
    def setUp(self):
        self.url = "http://example.com/file.zip"
        self.output_path = "/path/to/output/file.zip"
        self.mode = "wb"

    @mockpatch("challenges.challenge_config_utils.requests.get")
    @mockpatch("challenges.challenge_config_utils.write_file")
    def test_io_error(self, mock_write_file, mock_requests_get):
        mock_requests_get.return_value = Mock(
            status_code=200, content=b"file content"
        )
        mock_write_file.side_effect = IOError

        is_success, message = download_and_write_file(
            self.url, True, self.output_path, self.mode
        )

        self.assertFalse(is_success)
        self.assertEqual(
            message,
            "Unable to process the uploaded zip file. Please try again!",
        )

    @mockpatch("challenges.challenge_config_utils.requests.get")
    def test_request_exception(self, mock_requests_get):
        mock_requests_get.side_effect = requests.exceptions.RequestException

        is_success, message = download_and_write_file(
            self.url, True, self.output_path, self.mode
        )

        self.assertFalse(is_success)
        self.assertEqual(
            message,
            "A server error occured while processing zip file. Please try again!",
        )


@pytest.mark.django_db
class TestValidateChallengeConfigUtil0(unittest.TestCase):
    def setUp(self):
        self.request = Mock()
        # Create a challenge host team
        self.user = User.objects.create_user(
            username="testuser", password="12345"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.base_location = "/path/to/base"
        self.unique_folder_name = "unique_folder"
        self.extracted_folder_name = "extracted_folder"
        self.zip_ref = Mock()
        self.zip_ref.namelist.return_value = (
            []
        )  # Mock the namelist method to return an empty list
        self.current_challenge = Mock()
        self.error_message_dict = {
            "no_yaml_file": "No YAML file found in the zip.",
            "multiple_yaml_files": "Multiple YAML files found: {}.",
            "yaml_file_read_error": "YAML file read error: {} at line {}, column {}.",
            "missing_challenge_description": "Challenge description is missing.",
            "missing_evaluation_details": "Evaluation details are missing.",
            "missing_terms_and_conditions": "Terms and conditions are missing.",
            "missing_submission_guidelines": "Submission guidelines are missing.",
            "evaluation_script_not_zip": "Evaluation script is not a zip file.",
            "missing_evaluation_script": "Evaluation script file is missing.",
            "missing_evaluation_script_key": (
                "ERROR: There is no key for the evaluation script in the YAML file."
                " Please add it and then try again!"
            ),
            "missing_date": "Start date or end date is missing.",
            "start_date_greater_than_end_date": "Start date is greater than end date.",
            "challenge_metadata_schema_errors": "Schema errors: {}",
        }

        self.error_message_dict.update(
            {
                "missing_keys_in_challenge_phase_splits": (
                    "The following keys are missing in the challenge phase splits of YAML file (phase_split: {}): {}"
                ),
                "challenge_phase_split_not_found": (
                    "Challenge phase split (leaderboard_id: {}, challenge_phase_id: {}, dataset_split_id: {}) "
                    "not found in config."
                    "Deletion of existing challenge phase split after challenge creation is not allowed."
                ),
                "duplicate_combinations_in_challenge_phase_splits": (
                    "Duplicate combinations of leaderboard_id {}, challenge_phase_id {} and "
                    "dataset_split_id {} found in challenge phase splits."
                ),
                "challenge_phase_split_not_exist": (
                    "Challenge phase split (leaderboard_id: {}, challenge_phase_id: {}, dataset_split_id: {})"
                    " doesn't exist."
                    "Addition of challenge phase split after challenge creation is not allowed."
                ),
                "no_key_for_challenge_phase_splits": "There is no key for challenge phase splits.",
            }
        )

        self.util = ValidateChallengeConfigUtil(
            self.request,
            self.challenge_host_team,
            self.base_location,
            self.unique_folder_name,
            self.zip_ref,
            self.current_challenge,
        )
        self.util.error_messages_dict = self.error_message_dict
        self.util.yaml_file_data = {}
        self.util.extracted_folder_name = self.extracted_folder_name
        self.util.challenge_image_file = (
            Mock()
        )  # Initialize the missing attribute
        self.util.challenge_evaluation_script_file = (
            Mock()
        )  # Initialize if needed
        self.util.extracted_folder_name = "extracted_folder"
        self.util.error_messages = []
        self.request.data = {"GITHUB_REPOSITORY": "some_repo"}

    def test_no_yaml_file(self):
        self.util.yaml_file_count = 0

        result = self.util.read_and_validate_yaml()

        self.assertFalse(result)
        self.assertIn(
            "No YAML file found in the zip.", self.util.error_messages
        )

    def test_multiple_yaml_files(self):
        self.util.yaml_file_count = 2

        result = self.util.read_and_validate_yaml()

        self.assertFalse(result)
        self.assertIn(
            "Multiple YAML files found: 2.", self.util.error_messages
        )

    @mockpatch("challenges.challenge_config_utils.read_yaml_file")
    def test_yaml_read_error(self, mock_read_yaml_file):
        self.util.yaml_file_count = 1
        self.util.yaml_file = "config.yaml"
        mock_read_yaml_file.side_effect = yaml.YAMLError("None")

        result = self.util.read_and_validate_yaml()

        self.assertFalse(result)
        self.assertIn(
            "YAML file read error: None at line None, column None.",
            self.util.error_messages,
        )

    @mockpatch("challenges.challenge_config_utils.isfile")
    @mockpatch("challenges.challenge_config_utils.get_file_content")
    def test_validate_challenge_logo_valid_image(
        self, mock_get_file_content, mock_isfile
    ):
        self.util.yaml_file_data = {"image": "logo.png"}
        mock_isfile.return_value = True
        mock_get_file_content.return_value = b"image content"

        self.util.validate_challenge_logo()

        expected_path = join(
            self.base_location,
            self.unique_folder_name,
            self.extracted_folder_name,
            "logo.png",
        )
        self.assertEqual(self.util.challenge_image_path, expected_path)
        self.assertIsNotNone(self.util.challenge_image_file)
        self.assertEqual(
            self.util.files["challenge_image_file"].name, "logo.png"
        )

    @mockpatch("challenges.challenge_config_utils.isfile")
    def test_validate_challenge_logo_invalid_image(self, mock_isfile):
        self.util.yaml_file_data = {"image": "logo.txt"}
        mock_isfile.return_value = False

        self.util.validate_challenge_logo()

        self.assertIsNone(self.util.challenge_image_file)
        self.assertIsNone(self.util.files["challenge_image_file"])

    def test_validate_challenge_logo_no_image_key(self):
        self.util.yaml_file_data = {}

        self.util.validate_challenge_logo()

        self.assertIsNone(self.util.challenge_image_file)
        self.assertIsNone(self.util.files["challenge_image_file"])

    @pytest.mark.django_db
    @mockpatch("challenges.challenge_config_utils.ValidateChallengeConfigUtil")
    def test_validate_challenge_config_util_invalid_yaml(
        self, MockValidateChallengeConfigUtil
    ):
        # Arrange
        mock_instance = MockValidateChallengeConfigUtil.return_value
        mock_instance.valid_yaml = False
        mock_instance.error_messages = ["Error message"]
        mock_instance.yaml_file_data = {"key": "value"}
        mock_instance.files = {"file_key": "file_value"}

        request = Mock()
        challenge_host_team = 1
        BASE_LOCATION = "/path/to/base"
        unique_folder_name = "unique_folder"
        zip_ref = Mock()
        current_challenge = Mock()

        # Act
        result = validate_challenge_config_util(
            request,
            challenge_host_team,
            BASE_LOCATION,
            unique_folder_name,
            zip_ref,
            current_challenge,
        )

        # Assert
        self.assertEqual(
            result,
            (["Error message"], {"key": "value"}, {"file_key": "file_value"}),
        )

    @pytest.mark.django_db
    @mockpatch("challenges.challenge_config_utils.ValidateChallengeConfigUtil")
    def test_validate_challenge_config_util_with_current_challenge(
        self, MockValidateChallengeConfigUtil
    ):
        # Arrange
        mock_instance = MockValidateChallengeConfigUtil.return_value
        mock_instance.valid_yaml = True
        mock_instance.error_messages = []
        mock_instance.yaml_file_data = {"key": "value"}
        mock_instance.files = {"file_key": "file_value"}

        request = Mock()
        challenge_host_team = 1
        BASE_LOCATION = "/path/to/base"
        unique_folder_name = "unique_folder"
        zip_ref = Mock()
        current_challenge = Mock(id=1)

        # Mock the ChallengePhase objects
        challenge_phase1 = Mock(id=1, challenge=current_challenge.id)
        challenge_phase2 = Mock(id=2, challenge=current_challenge.id)
        current_challenge_phases = [challenge_phase1, challenge_phase2]

        # Mock the ChallengePhaseSplit objects
        challenge_phase_split1 = Mock(
            id=1,
            challenge_phase=challenge_phase1,
            leaderboard=Mock(id=1),
            dataset_split=Mock(id=1),
        )
        challenge_phase_split2 = Mock(
            id=2,
            challenge_phase=challenge_phase2,
            leaderboard=Mock(id=2),
            dataset_split=Mock(id=2),
        )
        current_challenge_phase_splits = [
            challenge_phase_split1,
            challenge_phase_split2,
        ]

        # Mock the Leaderboard objects
        leaderboard1 = Mock(id=1, config_id=1)
        leaderboard2 = Mock(id=2, config_id=2)
        current_leaderboards = [leaderboard1, leaderboard2]

        # Mock the DatasetSplit objects
        dataset_split1 = Mock(id=1, config_id=1)
        dataset_split2 = Mock(id=2, config_id=2)
        current_dataset_splits = [dataset_split1, dataset_split2]

        # Patch the model queries
        with mockpatch.object(
            ChallengePhase, "objects"
        ) as mock_challenge_phase_objects:
            mock_challenge_phase_objects.filter.return_value = (
                current_challenge_phases
            )

        with mockpatch.object(
            ChallengePhaseSplit, "objects"
        ) as mock_challenge_phase_split_objects:
            mock_challenge_phase_split_objects.filter.return_value = (
                current_challenge_phase_splits
            )

        with mockpatch.object(
            Leaderboard, "objects"
        ) as mock_leaderboard_objects:
            mock_leaderboard_objects.filter.return_value = current_leaderboards

        with mockpatch.object(
            DatasetSplit, "objects"
        ) as mock_dataset_split_objects:
            mock_dataset_split_objects.filter.return_value = (
                current_dataset_splits
            )

        # Act
        error_messages, yaml_file_data, files = validate_challenge_config_util(
            request,
            challenge_host_team,
            BASE_LOCATION,
            unique_folder_name,
            zip_ref,
            current_challenge,
        )

        # Assert
        self.assertEqual(error_messages, [])
        self.assertEqual(yaml_file_data, {"key": "value"})
        self.assertEqual(files, {"file_key": "file_value"})

    @mockpatch("challenges.challenge_config_utils.ValidateChallengeConfigUtil")
    def test_validate_challenge_config_util_without_current_challenge(
        self, MockValidateChallengeConfigUtil
    ):
        # Arrange
        mock_instance = MockValidateChallengeConfigUtil.return_value
        mock_instance.valid_yaml = True
        mock_instance.error_messages = []
        mock_instance.yaml_file_data = {"key": "value"}
        mock_instance.files = {"file_key": "file_value"}

        request = Mock()
        challenge_host_team = 1
        BASE_LOCATION = "/path/to/base"
        unique_folder_name = "unique_folder"
        zip_ref = Mock()
        current_challenge = None

        # Act
        error_messages, yaml_file_data, files = validate_challenge_config_util(
            request,
            challenge_host_team,
            BASE_LOCATION,
            unique_folder_name,
            zip_ref,
            current_challenge,
        )

        # Assert
        self.assertEqual(error_messages, [])
        self.assertEqual(yaml_file_data, {"key": "value"})
        self.assertEqual(files, {"file_key": "file_value"})

    def test_validate_challenge_description_missing(self):
        self.util.validate_challenge_description()
        self.assertIn(
            "Challenge description is missing.", self.util.error_messages
        )

    def test_validate_evaluation_details_file_missing(self):
        self.util.validate_evaluation_details_file()
        self.assertIn(
            "Evaluation details are missing.", self.util.error_messages
        )

    def test_validate_terms_and_conditions_file_missing(self):
        self.util.validate_terms_and_conditions_file()
        self.assertIn(
            "Terms and conditions are missing.", self.util.error_messages
        )

    def test_validate_submission_guidelines_file_missing(self):
        self.util.validate_submission_guidelines_file()
        self.assertIn(
            "Submission guidelines are missing.", self.util.error_messages
        )

    def test_validate_challenge_description_empty(self):
        self.util.yaml_file_data["description"] = ""
        self.util.validate_challenge_description()
        self.assertIn(
            "Challenge description is missing.", self.util.error_messages
        )

    def test_validate_evaluation_details_file_empty(self):
        self.util.yaml_file_data["evaluation_details"] = ""
        self.util.validate_evaluation_details_file()
        self.assertIn(
            "Evaluation details are missing.", self.util.error_messages
        )

    def test_validate_terms_and_conditions_file_empty(self):
        self.util.yaml_file_data["terms_and_conditions"] = ""
        self.util.validate_terms_and_conditions_file()
        self.assertIn(
            "Terms and conditions are missing.", self.util.error_messages
        )

    def test_validate_submission_guidelines_file_empty(self):
        self.util.yaml_file_data["submission_guidelines"] = ""
        self.util.validate_submission_guidelines_file()
        self.assertIn(
            "Submission guidelines are missing.", self.util.error_messages
        )

    def test_validate_evaluation_script_file_not_zip(self):
        self.util.yaml_file_data["evaluation_script"] = "script.txt"
        self.util.validate_evaluation_script_file()
        self.assertIn(
            "Evaluation script is not a zip file.", self.util.error_messages
        )

    def test_validate_dates_missing_dates(self):
        self.util.yaml_file_data = {"start_date": None, "end_date": None}
        self.util.validate_dates()
        self.assertIn(
            "Start date or end date is missing.", self.util.error_messages
        )

    def test_validate_dates_start_date_greater_than_end_date(self):
        self.util.yaml_file_data = {
            "start_date": "2023-12-31",
            "end_date": "2023-01-01",
        }
        self.util.validate_dates()
        self.assertIn(
            "Start date is greater than end date.", self.util.error_messages
        )

    def test_validate_dates_valid_dates(self):
        self.util.yaml_file_data = {
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }
        self.util.validate_dates()
        self.assertNotIn(
            "Start date or end date is missing.", self.util.error_messages
        )
        self.assertNotIn(
            "Start date is greater than end date.", self.util.error_messages
        )

    @mockpatch(
        "challenges.serializers.ZipChallengeSerializer.is_valid",
        return_value=False,
    )
    @mockpatch(
        "challenges.serializers.ZipChallengeSerializer.errors",
        new_callable=Mock,
        return_value={"field": ["error"]},
    )
    def test_validate_serializer_invalid(self, mock_errors, mock_is_valid):
        self.util.validate_serializer()
        self.assertEqual(len(self.util.error_messages), 1)
        self.assertIn("Schema errors:", self.util.error_messages[0])

    def test_validate_challenge_phase_splits_uuid_not_found(self):
        self.util.yaml_file_data = {
            "challenge_phase_splits": [
                {
                    "is_leaderboard_order_descending": True,
                    "leaderboard_decimal_precision": 2,
                    "visibility": 1,
                    "dataset_split_id": 1,
                    "leaderboard_id": 2,
                    "challenge_phase_id": 3,
                }
            ]
        }
        self.util.phase_ids = [3]
        self.util.leaderboard_ids = [2]
        self.util.dataset_splits_ids = [1]
        self.util.error_messages = []

        self.util.validate_challenge_phase_splits(
            [(99, 98, 97)],
            current_phase_config_ids=[],
            current_leaderboard_config_ids=[2],
            current_dataset_config_ids=[1],
        )

        assert any(
            "challenge phase split" in msg.lower()
            and "not found in config" in msg.lower()
            for msg in self.util.error_messages
        )

    def test_validate_challenge_phase_splits_duplicate_combinations(self):
        self.util.yaml_file_data = {
            "challenge_phase_splits": [
                {
                    "is_leaderboard_order_descending": True,
                    "leaderboard_decimal_precision": 2,
                    "visibility": 1,
                    "dataset_split_id": 1,
                    "leaderboard_id": 2,
                    "challenge_phase_id": 3,
                },
                {
                    "is_leaderboard_order_descending": True,
                    "leaderboard_decimal_precision": 2,
                    "visibility": 1,
                    "dataset_split_id": 1,
                    "leaderboard_id": 2,
                    "challenge_phase_id": 3,
                },
            ]
        }
        self.util.phase_ids = [3]
        self.util.leaderboard_ids = [2]
        self.util.dataset_splits_ids = [1]
        self.util.error_messages = []
        self.util.validate_challenge_phase_splits([])
        assert any(
            "Duplicate combinations of leaderboard_id" in msg
            for msg in self.util.error_messages
        )

    def test_validate_challenge_phase_splits_invalid_mapping(self):
        self.util.yaml_file_data = {
            "challenge_phase_splits": [
                {
                    "is_leaderboard_order_descending": True,
                    "leaderboard_decimal_precision": 2,
                    "visibility": 1,
                    "dataset_split_id": 99,  # not in dataset_splits_ids
                    "leaderboard_id": 2,
                    "challenge_phase_id": 3,
                }
            ]
        }
        self.util.phase_ids = [3]
        self.util.leaderboard_ids = [2]
        self.util.dataset_splits_ids = [1]
        self.util.error_messages = []
        self.util.validate_challenge_phase_splits([])
        assert any(
            "Invalid dataset split id" in msg
            for msg in self.util.error_messages
        )

    def test_validate_evaluation_script_file_missing_key(self):
        # Remove 'evaluation_script' key to trigger the else branch
        self.util.yaml_file_data = {}
        self.util.validate_evaluation_script_file()
        assert any(
            "There is no key for the evaluation script in the YAML file" in msg
            for msg in self.util.error_messages
        )

    def test_read_yaml_file(self):
        data = {"foo": "bar"}
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            yaml.dump(data, f)
            f.flush()
            result = read_yaml_file(f.name, "r")
        self.assertEqual(result, data)

    def test_get_yaml_read_error_with_problem_and_mark(self):
        class MockExc:
            problem = "some problem"

            class Mark:
                line = 2
                column = 3

            problem_mark = Mark()

        desc, line, col = get_yaml_read_error(MockExc())
        self.assertEqual(desc, "Some problem")
        self.assertEqual(line, 3)
        self.assertEqual(col, 4)

    def test_get_yaml_read_error_without_problem(self):
        class MockExc:
            pass

        desc, line, col = get_yaml_read_error(MockExc())
        self.assertIsNone(desc)
        self.assertIsNone(line)
        self.assertIsNone(col)

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=False)
    def test_is_challenge_config_yaml_html_field_valid_file_not_found(
        self, mock_isfile
    ):
        yaml_file_data = {"desc": "nofile.html"}
        is_valid, msg = is_challenge_config_yaml_html_field_valid(
            yaml_file_data, "desc", "/tmp"
        )
        self.assertFalse(is_valid)
        self.assertIn("not found", msg)

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=True)
    def test_is_challenge_config_yaml_html_field_valid_not_html(
        self, mock_isfile
    ):
        yaml_file_data = {"desc": "file.txt"}
        is_valid, msg = is_challenge_config_yaml_html_field_valid(
            yaml_file_data, "desc", "/tmp"
        )
        self.assertFalse(is_valid)
        self.assertIn("not a HTML file", msg)

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=True)
    def test_is_challenge_config_yaml_html_field_valid_success(
        self, mock_isfile
    ):
        yaml_file_data = {"desc": "file.html"}
        s_valid, msg = is_challenge_config_yaml_html_field_valid(
            yaml_file_data, "desc", "/tmp"
        )
        self.assertTrue(s_valid)
        self.assertEqual(msg, "")

    def test_is_challenge_phase_config_yaml_html_field_valid_present(self):
        yaml_file_data = {"desc": "foo", "name": "phase"}
        s_valid, msg = is_challenge_phase_config_yaml_html_field_valid(
            yaml_file_data, "desc", "/tmp"
        )
        self.assertTrue(s_valid)
        self.assertEqual(msg, "")

    def test_is_challenge_phase_config_yaml_html_field_valid_missing(self):
        yaml_file_data = {"name": "phase"}
        is_valid, msg = is_challenge_phase_config_yaml_html_field_valid(
            yaml_file_data, "desc", "/tmp"
        )
        self.assertFalse(is_valid)
        self.assertIn("There is no key for desc in phase phase", msg)

    @mockpatch("challenges.challenge_config_utils.requests.get")
    @mockpatch("challenges.challenge_config_utils.write_file")
    def test_download_and_write_file_success(
        self, mock_write_file, mock_requests_get
    ):
        mock_requests_get.return_value = Mock(status_code=200, content=b"abc")
        is_success, msg = download_and_write_file(
            "http://x", True, "/tmp/file", "wb"
        )
        self.assertTrue(is_success)
        self.assertIsNone(msg)

    @mockpatch("challenges.challenge_config_utils.requests.get")
    def test_download_and_write_file_request_exception(
        self, mock_requests_get
    ):
        mock_requests_get.side_effect = requests.exceptions.RequestException
        is_success, msg = download_and_write_file(
            "http://x", True, "/tmp/file", "wb"
        )
        self.assertFalse(is_success)
        self.assertIn("server error", msg)

    def test_is_challenge_phase_split_mapping_valid_all_valid(self):
        phase_ids = [1]
        leaderboard_ids = [2]
        dataset_split_ids = [3]
        phase_split = {
            "challenge_phase_id": 1,
            "leaderboard_id": 2,
            "dataset_split_id": 3,
        }
        is_success, errors = is_challenge_phase_split_mapping_valid(
            phase_ids, leaderboard_ids, dataset_split_ids, phase_split, 0
        )
        self.assertTrue(is_success)
        self.assertEqual(errors, [])

    def test_is_challenge_phase_split_mapping_valid_invalid(self):
        phase_ids = [1]
        leaderboard_ids = [2]
        dataset_split_ids = [3]
        phase_split = {
            "challenge_phase_id": 9,
            "leaderboard_id": 8,
            "dataset_split_id": 7,
        }
        is_success, errors = is_challenge_phase_split_mapping_valid(
            phase_ids, leaderboard_ids, dataset_split_ids, phase_split, 0
        )
        self.assertFalse(is_success)
        self.assertTrue(any("Invalid" in e for e in errors))

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=True)
    @mockpatch(
        "challenges.challenge_config_utils.get_file_content",
        return_value=b"abc",
    )
    def test_get_value_from_field_html(
        self, mock_get_file_content, mock_isfile
    ):
        data = {"desc": "file.html"}
        val = get_value_from_field(data, "/tmp", "desc")
        self.assertEqual(val, "abc")

    @mockpatch("challenges.challenge_config_utils.isfile", return_value=False)
    def test_get_value_from_field_not_html(self, mock_isfile):
        data = {"desc": "file.txt"}
        val = get_value_from_field(data, "/tmp", "desc")
        self.assertIsNone(val)


@pytest.mark.django_db
class TestValidateChallengeConfigUtil(unittest.TestCase):
    def setUp(self):
        self.request = Mock()
        self.user = User.objects.create_user(
            username="testuser", password="12345"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.base_location = "/path/to/base"
        self.unique_folder_name = "unique_folder"
        self.extracted_folder_name = "extracted_folder"
        self.zip_ref = Mock()
        self.zip_ref.namelist.return_value = []
        self.current_challenge = Mock()
        self.util = ValidateChallengeConfigUtil(
            self.request,
            self.challenge_host_team,
            self.base_location,
            self.unique_folder_name,
            self.zip_ref,
            self.current_challenge,
        )
        self.util.error_messages_dict = {
            "missing_leaderboard_id": "Leaderboard ID is missing.",
            "missing_leaderboard_schema": "Leaderboard schema is missing.",
            "missing_leaderboard_labels": "Leaderboard labels are missing.",
            "missing_leaderboard_default_order_by": "Default order by is missing.",
            "incorrect_default_order_by": "Default order by is incorrect.",
            "invalid_leaderboard_schema": "Invalid leaderboard schema.",
            "missing_leaderboard_key": "Leaderboard key is missing.",
            "leaderboard_schema_error": "Leaderboard schema error for leaderboard with ID: {}",
            "leaderboard_deletion_after_creation": "Cannot delete leaderboard after challenge creation.",
            "missing_challenge_phases": "Missing challenge phases.",
            "no_codename_for_challenge_phase": "Codename is missing for challenge phase.",
            "duplicate_codename_for_phase": "Duplicate codename '{}' for phase '{}'.",
            "no_test_annotation_file_found": "No test annotation file found for phase '{}'.",
            "is_submission_public_restricted": (
                "Submission is public but restricted to select one submission for phase '{}'."
            ),
            "missing_dates_challenge_phase": "Missing start or end date for phase '{}'.",
            "start_date_greater_than_end_date_challenge_phase": "Start date is greater than end date for phase '{}'.",
            "missing_option_in_submission_meta_attribute": (
                "Missing options in submission meta attribute for phase '{}'."
            ),
            "invalid_submission_meta_attribute_types": "Invalid submission meta attribute type '{}' for phase '{}'.",
            "missing_fields_in_submission_meta_attribute": (
                "Missing fields '{}' in submission meta attribute for phase '{}'."
            ),
            "challenge_phase_schema_errors": "Challenge phase schema errors: {} - {}",
            "challenge_phase_addition": "Cannot add new challenge phase after challenge creation for phase '{}'.",
            "challenge_phase_not_found": "Challenge phase '{}' not found.",
            "extra_tags": "Too many tags provided.",
            "wrong_domain": "Invalid domain provided.",
            "sponsor_not_found": "Sponsor name or website not found.",
            "prize_not_found": "Prize rank or amount not found.",
            "duplicate_rank": "Duplicate rank found: {}.",
            "prize_rank_wrong": "Invalid prize rank: {}.",
            "prize_amount_wrong": "Invalid prize amount: {}.",
        }
        self.util.yaml_file_data = {}
        self.util.extracted_folder_name = self.extracted_folder_name
        self.util.error_messages = []
        self.util.challenge_phase_split = Mock()
        self.util.challenge_config_location = (
            "/path/to/config"  # Set a valid path here
        )

    def test_missing_leaderboard_id(self):
        self.util.yaml_file_data = {"leaderboard": [{}]}
        self.util.validate_leaderboards([])
        self.assertIn("Leaderboard ID is missing.", self.util.error_messages)

    def test_missing_leaderboard_schema(self):
        self.util.yaml_file_data = {"leaderboard": [{"id": "test_id"}]}
        self.util.validate_leaderboards([])
        self.assertIn(
            "Leaderboard schema is missing.", self.util.error_messages
        )

    def test_missing_leaderboard_labels(self):
        self.util.yaml_file_data = {
            "leaderboard": [{"id": "test_id", "schema": {}}]
        }
        self.util.validate_leaderboards([])
        self.assertIn(
            "Leaderboard labels are missing.", self.util.error_messages
        )

    def test_missing_leaderboard_default_order_by(self):
        self.util.yaml_file_data = {
            "leaderboard": [{"id": "test_id", "schema": {"labels": []}}]
        }
        self.util.validate_leaderboards([])
        self.assertIn("Default order by is missing.", self.util.error_messages)

    def test_incorrect_default_order_by(self):
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": "test_id",
                    "schema": {"labels": ["a", "b"], "default_order_by": "c"},
                }
            ]
        }
        self.util.validate_leaderboards([])
        self.assertIn(
            "Default order by is incorrect.", self.util.error_messages
        )

    def test_leaderboard_schema_error(self):
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": "test_id",
                    "schema": {"labels": ["a", "b"], "default_order_by": "a"},
                }
            ]
        }
        with mockpatch(
            "challenges.serializers.LeaderboardSerializer.is_valid",
            return_value=False,
        ):
            with mockpatch(
                "challenges.serializers.LeaderboardSerializer.errors",
                new_callable=Mock,
                return_value="some_error",
            ):
                self.util.validate_leaderboards([])
                self.assertEqual(
                    self.util.error_messages[0],
                    self.util.error_messages_dict[
                        "leaderboard_schema_error"
                    ].format("test_id", "some_error"),
                )

    @mockpatch("challenges.challenge_config_utils.LeaderboardSerializer")
    def test_leaderboard_addition_after_creation(self, MockSerializer):
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": 1,
                    "schema": {"labels": ["z"], "default_order_by": "z"},
                },
                {
                    "id": 99,
                    "schema": {"labels": ["a"], "default_order_by": "a"},
                },
            ]
        }
        self.util.validate_leaderboards([1])
        self.assertEqual(self.util.error_messages, [])

    @mockpatch("challenges.challenge_config_utils.LeaderboardSerializer")
    def test_leaderboard_addition_after_creation_with_multiple_leaderboards(
        self, MockSerializer
    ):
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": 1,
                    "schema": {"labels": ["z"], "default_order_by": "z"},
                },
                {
                    "id": 99,
                    "schema": {"labels": ["a"], "default_order_by": "a"},
                },
                {
                    "id": 100,
                    "schema": {"labels": ["b"], "default_order_by": "b"},
                },
            ]
        }
        self.util.validate_leaderboards([1])
        self.assertEqual(self.util.error_messages, [])

    @mockpatch.object(
        ValidateChallengeConfigUtil, "_locked_leaderboard_modified_message"
    )
    @mockpatch("challenges.challenge_config_utils.LeaderboardSerializer")
    def test_existing_leaderboard_checked_when_challenge_approved(
        self, MockSerializer, mock_locked_msg
    ):
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        mock_locked_msg.return_value = "LOCKED_LB"
        self.current_challenge.approved_by_admin = True
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": 1,
                    "schema": {"labels": ["z"], "default_order_by": "z"},
                },
            ]
        }
        self.util.validate_leaderboards([1])
        mock_locked_msg.assert_called_once()
        self.assertIn("LOCKED_LB", self.util.error_messages)
        self.assertIn(1, self.util.leaderboard_ids)

    @mockpatch.object(
        ValidateChallengeConfigUtil, "_locked_leaderboard_modified_message"
    )
    @mockpatch("challenges.challenge_config_utils.LeaderboardSerializer")
    def test_existing_leaderboard_lock_skipped_without_admin_approval(
        self, MockSerializer, mock_locked_msg
    ):
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        self.current_challenge.approved_by_admin = False
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": 1,
                    "schema": {"labels": ["z"], "default_order_by": "z"},
                },
            ]
        }
        self.util.validate_leaderboards([1])
        mock_locked_msg.assert_not_called()
        self.assertEqual(self.util.error_messages, [])
        self.assertIn(1, self.util.leaderboard_ids)

    def test_leaderboard_deletion_after_creation(self):
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": "test_id",
                    "schema": {"labels": ["a"], "default_order_by": "a"},
                }
            ]
        }
        self.util.validate_leaderboards(["test_id", "deleted_leaderboard_id"])
        self.assertIn(
            "Leaderboard schema error for leaderboard with ID: test_id",
            self.util.error_messages[0],
        )

    def test_missing_leaderboard_key(self):
        self.util.yaml_file_data = {}
        self.util.validate_leaderboards([])
        self.assertEqual(
            self.util.error_messages[0],
            self.util.error_messages_dict["missing_leaderboard_key"],
        )

    def test_missing_challenge_phases(self):
        self.util.yaml_file_data = {}
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0], "Missing challenge phases."
        )

    def test_no_codename_for_challenge_phase(self):
        self.util.yaml_file_data = {
            "challenge_phases": [{"name": "Phase 1", "id": 1}]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Codename is missing for challenge phase.",
        )

    def test_no_test_annotation_file_found(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "test_annotation_file": "non_existent_file",
                    "id": 1,
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "No test annotation file found for phase 'Phase 1'.",
        )

    def test_is_submission_public_restricted(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "is_submission_public": True,
                    "is_restricted_to_select_one_submission": True,
                    "id": 1,
                    "description": "Description 1",
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Submission is public but restricted to select one submission for phase 'Phase 1'.",
        )

    def test_duplicate_codename_for_phase(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 1,
                    "start_date": "2023-10-10T00:00:00",
                    "end_date": "2023-10-11T00:00:00",
                    "max_submissions_per_month": 10,
                    "description": "Description 1",
                },
                {
                    "codename": "phase1",
                    "name": "Phase 2",
                    "id": 2,
                    "start_date": "2023-10-12T00:00:00",
                    "end_date": "2023-10-13T00:00:00",
                    "max_submissions_per_month": 10,
                    "description": "Description 2",
                },
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertIn(
            "Duplicate codename 'phase1' for phase 'Phase 2'.",
            self.util.error_messages,
        )

    def test_missing_dates_challenge_phase(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 1,
                    "description": "Description 1",
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Missing start or end date for phase '1'.",
        )

    def test_start_date_greater_than_end_date_challenge_phase(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "start_date": "2023-10-10",
                    "end_date": "2023-10-09",
                    "id": 1,
                    "description": "Description 1",
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Start date is greater than end date for phase '1'.",
        )

    def test_missing_option_in_submission_meta_attribute(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 1,
                    "description": "Description 1",
                    "submission_meta_attributes": [
                        {"name": "attr1", "type": "radio"}
                    ],
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Missing start or end date for phase '1'.",
        )

    def test_invalid_submission_meta_attribute_types(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 1,
                    "description": "Description 1",
                    "start_date": "2023-10-10T00:00:00",
                    "end_date": "2023-10-11T00:00:00",
                    "submission_meta_attributes": [
                        {"name": "attr1", "type": "invalid_type"}
                    ],
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Missing fields '1' in submission meta attribute for phase 'description'.",
        )

    def test_missing_fields_in_submission_meta_attribute(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 1,
                    "description": "Description 1",
                    "start_date": "2023-10-10T00:00:00",
                    "end_date": "2023-10-11T00:00:00",
                    "submission_meta_attributes": [{"type": "text"}],
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertEqual(
            self.util.error_messages[0],
            "Missing fields '1' in submission meta attribute for phase 'name, description'.",
        )

    def test_challenge_phase_schema_errors(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 1,
                    "description": "Description 1",
                    "start_date": "2023-10-10T00:00:00",
                    "end_date": "2023-10-11T00:00:00",
                    "invalid_field": "invalid_value",
                }
            ]
        }
        self.util.validate_challenge_phases([])
        self.assertIn(
            "Challenge phase schema errors: 1 - ", self.util.error_messages[0]
        )

    def test_challenge_phase_addition(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 9,
                    "description": "Description 1",
                    "max_submissions_per_month": 10,
                    "start_date": "2023-10-10T00:00:00",
                    "end_date": "2023-10-11T00:00:00",
                    "submission_meta_attributes": [
                        {
                            "name": "attr1",
                            "description": "Description 1",
                            "type": "text",
                        }
                    ],
                }
            ]
        }
        self.util.validate_challenge_phases([2])
        self.assertEqual(
            self.util.error_messages[0],
            "Challenge phase schema errors: 9 - "
            "{'description': [ErrorDetail(string='This field may not be null.', code='null')]}",
        )

    def test_challenge_phase_not_found(self):
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "codename": "phase1",
                    "name": "Phase 1",
                    "id": 3,
                    "description": "Description 1",
                    "max_submissions_per_month": 10,
                    "start_date": "2023-10-10T00:00:00",
                    "end_date": "2023-10-11T00:00:00",
                    "submission_meta_attributes": [
                        {
                            "name": "attr1",
                            "description": "Description 1",
                            "type": "text",
                        }
                    ],
                    "max_submissions_per_month": 10,
                }
            ]
        }
        self.util.validate_challenge_phases([2])
        self.assertEqual(
            self.util.error_messages[0],
            "Challenge phase schema errors: 3 -"
            " {'description': [ErrorDetail(string='This field may not be null.', code='null')]}",
        )

    def test_check_tags(self):
        # Test case for more than 4 tags
        self.util.yaml_file_data = {
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
        }
        self.util.check_tags()
        self.assertEqual(
            self.util.error_messages[0], "Too many tags provided."
        )

    def test_check_domain(self):
        # Test case for invalid domain
        self.util.yaml_file_data = {"domain": "invalid_domain"}
        self.util.check_domain()
        self.assertEqual(
            self.util.error_messages[0], "Invalid domain provided."
        )

    def test_check_sponsor(self):
        # Test case for missing sponsor name or website
        self.util.yaml_file_data = {
            "sponsors": [
                {"name": "Sponsor1"},
                {"website": "http://sponsor2.com"},
            ]
        }
        self.util.check_sponsor()
        self.assertEqual(
            self.util.error_messages[0], "Sponsor name or website not found."
        )

    def test_check_prizes(self):
        # Test case for valid prizes
        self.util.yaml_file_data = {
            "prizes": [
                {"rank": 1, "amount": "100USD"},
                {"rank": 2, "amount": "200USD"},
            ]
        }
        self.util.error_messages = []  # Clear the error messages list
        self.util.check_prizes()
        self.assertEqual(len(self.util.error_messages), 0)

        # Test case for duplicate rank
        self.util.yaml_file_data = {
            "prizes": [
                {"rank": 1, "amount": "100USD"},
                {"rank": 1, "amount": "200USD"},
            ]
        }
        self.util.error_messages = []  # Clear the error messages list
        self.util.check_prizes()
        self.assertEqual(len(self.util.error_messages), 1)
        self.assertEqual(
            self.util.error_messages[0], "Duplicate rank found: 1."
        )

        # Test case for invalid rank
        self.util.yaml_file_data = {
            "prizes": [
                {"rank": 0, "amount": "100USD"},
                {"rank": 0, "amount": "200USD"},
            ]
        }
        self.util.error_messages = []  # Clear the error messages list
        self.util.check_prizes()
        self.assertEqual(len(self.util.error_messages), 3)
        self.assertEqual(self.util.error_messages[0], "Invalid prize rank: 0.")

        # Test case for invalid amount
        self.util.yaml_file_data = {"prizes": [{"rank": 1, "amount": "100"}]}
        self.util.check_prizes()
        self.assertEqual(
            self.util.error_messages[3], "Invalid prize amount: 100."
        )

        # Test case for missing rank
        self.util.yaml_file_data = {
            "prizes": [{"rank": 1, "amount": "100USD"}]
        }
        self.util.error_messages = []  # Clear the error messages list
        self.util.check_prizes()
        self.assertEqual(
            len(self.util.error_messages), 0
        )  # No error messages expected


@override_settings(MEDIA_ROOT="/tmp/evalai-lock-coverage")
class TestApprovedConfigLockMessageCoverage(TestCase):
    """
    Cover _locked_* helpers and _stable_json for Codecov on post-approval
    immutability checks (real ORM queries, no mocks of the methods under test).
    """

    @staticmethod
    def _bare_util(challenge):
        util = ValidateChallengeConfigUtil.__new__(ValidateChallengeConfigUtil)
        util.current_challenge = challenge
        util.error_messages_dict = error_message_dict
        return util

    def setUp(self):
        os.makedirs("/tmp/evalai-lock-coverage", exist_ok=True)
        suffix = uuid.uuid4().hex[:12]
        self.user = User.objects.create_user(
            username="lockcovuser_{}".format(suffix), password="secret"
        )
        self.team = ChallengeHostTeam.objects.create(
            team_name="Lock Cov Host {}".format(suffix),
            created_by=self.user,
        )
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title="Lock Cov Challenge",
            short_description="s",
            description="d",
            terms_and_conditions="t",
            submission_guidelines="g",
            creator=self.team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            approved_by_admin=True,
        )
        self.lb = Leaderboard.objects.create(
            config_id=1,
            schema={
                "labels": ["yes/no", "overall"],
                "default_order_by": "overall",
            },
        )
        self.ds = DatasetSplit.objects.create(
            config_id=1,
            name="Split Name",
            codename="split_codename",
        )
        self.phase = ChallengePhase.objects.create(
            name="Phase 1",
            description="desc",
            leaderboard_public=False,
            is_public=False,
            start_date=now,
            end_date=now + timedelta(days=1),
            challenge=self.challenge,
            config_id=1,
            codename="p1",
            max_submissions_per_day=100,
            max_submissions=100,
            max_submissions_per_month=100,
            test_annotation=SimpleUploadedFile(
                "ann.txt", b"x", content_type="text/plain"
            ),
        )
        ChallengePhaseSplit.objects.create(
            challenge_phase=self.phase,
            leaderboard=self.lb,
            dataset_split=self.ds,
            visibility=ChallengePhaseSplit.PUBLIC,
            leaderboard_decimal_precision=2,
            is_leaderboard_order_descending=True,
        )
        self.phase.refresh_from_db()
        self.phase_annotation_basename = basename(
            self.phase.test_annotation.name
        )
        self.util = self._bare_util(self.challenge)

    def test_stable_json(self):
        self.assertEqual(
            ValidateChallengeConfigUtil._stable_json({"b": 1, "a": 2}),
            '{"a": 2, "b": 1}',
        )

    def test_approved_config_locked(self):
        self.assertTrue(self.util._approved_config_locked())
        self.challenge.approved_by_admin = False
        self.challenge.save()
        self.assertFalse(self.util._approved_config_locked())

    def test_locked_leaderboard_detects_schema_change(self):
        msg = self.util._locked_leaderboard_modified_message(
            {
                "id": 1,
                "schema": {"labels": ["x"], "default_order_by": "x"},
            }
        )
        self.assertIsNotNone(msg)
        self.assertIn("approved", msg.lower())

    def test_locked_leaderboard_none_when_schema_matches(self):
        msg = self.util._locked_leaderboard_modified_message(
            {
                "id": 1,
                "schema": {
                    "labels": ["yes/no", "overall"],
                    "default_order_by": "overall",
                },
            }
        )
        self.assertIsNone(msg)

    def test_locked_leaderboard_none_when_not_linked(self):
        Leaderboard.objects.create(
            config_id=99,
            schema={"labels": ["a"], "default_order_by": "a"},
        )
        msg = self.util._locked_leaderboard_modified_message(
            {"id": 99, "schema": {"labels": ["z"], "default_order_by": "z"}}
        )
        self.assertIsNone(msg)

    def test_locked_dataset_split_detects_change(self):
        msg = self.util._locked_dataset_split_modified_message(
            {"id": 1, "name": "Other", "codename": "split_codename"}
        )
        self.assertIsNotNone(msg)

    def test_locked_dataset_split_none_when_match(self):
        msg = self.util._locked_dataset_split_modified_message(
            {
                "id": 1,
                "name": "Split Name",
                "codename": "split_codename",
            }
        )
        self.assertIsNone(msg)

    def test_locked_challenge_phase_detects_name_change(self):
        msg = self.util._locked_challenge_phase_modified_message(
            {"id": 1, "name": "Renamed"}
        )
        self.assertIsNotNone(msg)

    def test_locked_challenge_phase_none_when_consistent(self):
        msg = self.util._locked_challenge_phase_modified_message(
            {
                "id": 1,
                "name": "Phase 1",
                "test_annotation_file": self.phase_annotation_basename,
            }
        )
        self.assertIsNone(msg)

    def test_locked_challenge_phase_detects_annotation_reference_change(self):
        msg = self.util._locked_challenge_phase_modified_message(
            {
                "id": 1,
                "name": "Phase 1",
                "test_annotation_file": "nonexistent_annotation.txt",
            }
        )
        self.assertIsNotNone(msg)

    def test_locked_challenge_phase_split_visibility_change(self):
        msg = self.util._locked_challenge_phase_split_modified_message(
            {
                "leaderboard_id": 1,
                "challenge_phase_id": 1,
                "dataset_split_id": 1,
                "visibility": ChallengePhaseSplit.HOST,
                "leaderboard_decimal_precision": 2,
                "is_leaderboard_order_descending": True,
            }
        )
        self.assertIsNotNone(msg)

    def test_locked_challenge_phase_split_precision_change(self):
        msg = self.util._locked_challenge_phase_split_modified_message(
            {
                "leaderboard_id": 1,
                "challenge_phase_id": 1,
                "dataset_split_id": 1,
                "visibility": ChallengePhaseSplit.PUBLIC,
                "leaderboard_decimal_precision": 5,
                "is_leaderboard_order_descending": True,
            }
        )
        self.assertIsNotNone(msg)

    def test_locked_challenge_phase_split_order_change(self):
        msg = self.util._locked_challenge_phase_split_modified_message(
            {
                "leaderboard_id": 1,
                "challenge_phase_id": 1,
                "dataset_split_id": 1,
                "visibility": ChallengePhaseSplit.PUBLIC,
                "leaderboard_decimal_precision": 2,
                "is_leaderboard_order_descending": False,
            }
        )
        self.assertIsNotNone(msg)

    def test_locked_challenge_phase_split_none_when_match(self):
        msg = self.util._locked_challenge_phase_split_modified_message(
            {
                "leaderboard_id": 1,
                "challenge_phase_id": 1,
                "dataset_split_id": 1,
                "visibility": ChallengePhaseSplit.PUBLIC,
                "leaderboard_decimal_precision": 2,
                "is_leaderboard_order_descending": True,
            }
        )
        self.assertIsNone(msg)

    def test_locked_challenge_phase_split_missing_row(self):
        msg = self.util._locked_challenge_phase_split_modified_message(
            {
                "leaderboard_id": 8,
                "challenge_phase_id": 8,
                "dataset_split_id": 8,
                "visibility": ChallengePhaseSplit.PUBLIC,
                "leaderboard_decimal_precision": 2,
                "is_leaderboard_order_descending": True,
            }
        )
        self.assertIsNone(msg)


MEDIA_APPROVED_VALIDATE = "/tmp/evalai-approved-validate"


@override_settings(MEDIA_ROOT=MEDIA_APPROVED_VALIDATE)
class TestApprovedValidateMethodsRealLockIntegration(TestCase):
    """
    Exercise validate_* approved-lock branches with a real Challenge graph
    (no mocking of _locked_*), raising Codecov on the call sites in
    challenge_config_utils.py.
    """

    def setUp(self):
        os.makedirs(MEDIA_APPROVED_VALIDATE, exist_ok=True)
        suffix = uuid.uuid4().hex[:12]
        self.user = User.objects.create_user(
            username="apvl_{}".format(suffix), password="secret"
        )
        self.team = ChallengeHostTeam.objects.create(
            team_name="Apv Host {}".format(suffix),
            created_by=self.user,
        )
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title="Apv Challenge",
            short_description="s",
            description="d",
            terms_and_conditions="t",
            submission_guidelines="g",
            creator=self.team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            approved_by_admin=True,
        )
        self.lb = Leaderboard.objects.create(
            config_id=1,
            schema={
                "labels": ["yes/no", "overall"],
                "default_order_by": "overall",
            },
        )
        self.ds = DatasetSplit.objects.create(
            config_id=1,
            name="Split Name",
            codename="split_codename",
        )
        self.phase = ChallengePhase.objects.create(
            name="Phase 1",
            description="desc",
            leaderboard_public=False,
            is_public=False,
            start_date=now,
            end_date=now + timedelta(days=1),
            challenge=self.challenge,
            config_id=1,
            codename="pv1",
            max_submissions_per_day=100,
            max_submissions=100,
            max_submissions_per_month=100,
            test_annotation=None,
        )
        # validate_challenge_phases replaces description with get_value_from_field;
        # it must resolve to the same string as phase.description for the lock check.
        self.phase_desc_html = "phase_desc_{}.html".format(suffix)
        with open(
            join(MEDIA_APPROVED_VALIDATE, self.phase_desc_html),
            "w",
            encoding="utf-8",
        ) as desc_file:
            desc_file.write("desc")
        ChallengePhaseSplit.objects.create(
            challenge_phase=self.phase,
            leaderboard=self.lb,
            dataset_split=self.ds,
            visibility=ChallengePhaseSplit.PUBLIC,
            leaderboard_decimal_precision=2,
            is_leaderboard_order_descending=True,
        )
        self.util = ValidateChallengeConfigUtil.__new__(
            ValidateChallengeConfigUtil
        )
        self.util.current_challenge = self.challenge
        self.util.error_messages_dict = error_message_dict
        self.util.error_messages = []
        self.util.leaderboard_ids = []
        self.util.phase_ids = []
        self.util.dataset_splits_ids = []
        self.util.challenge_config_location = MEDIA_APPROVED_VALIDATE
        self.util.files = {"challenge_test_annotation_files": []}

    @mockpatch("challenges.challenge_config_utils.LeaderboardSerializer")
    def test_validate_leaderboards_real_lock_no_error(self, mock_ls):
        mock_ls.return_value.is_valid.return_value = True
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": 1,
                    "schema": {
                        "labels": ["yes/no", "overall"],
                        "default_order_by": "overall",
                    },
                }
            ]
        }
        self.util.validate_leaderboards([1])
        self.assertEqual(self.util.error_messages, [])

    @mockpatch("challenges.challenge_config_utils.LeaderboardSerializer")
    def test_validate_leaderboards_real_lock_error(self, mock_ls):
        mock_ls.return_value.is_valid.return_value = True
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": 1,
                    "schema": {"labels": ["x"], "default_order_by": "x"},
                }
            ]
        }
        self.util.validate_leaderboards([1])
        self.assertTrue(self.util.error_messages)

    @mockpatch("challenges.challenge_config_utils.DatasetSplitSerializer")
    def test_validate_dataset_splits_real_lock_no_error(self, mock_dss):
        mock_dss.return_value.is_valid.return_value = True
        self.util.yaml_file_data = {
            "dataset_splits": [
                {
                    "id": 1,
                    "name": "Split Name",
                    "codename": "split_codename",
                }
            ]
        }
        self.util.validate_dataset_splits([1])
        self.assertEqual(self.util.error_messages, [])

    @mockpatch("challenges.challenge_config_utils.DatasetSplitSerializer")
    def test_validate_dataset_splits_real_lock_error(self, mock_dss):
        mock_dss.return_value.is_valid.return_value = True
        self.util.yaml_file_data = {
            "dataset_splits": [
                {
                    "id": 1,
                    "name": "Other Name",
                    "codename": "split_codename",
                }
            ]
        }
        self.util.validate_dataset_splits([1])
        self.assertTrue(self.util.error_messages)

    @mockpatch(
        "challenges.challenge_config_utils.ChallengePhaseCreateSerializer"
    )
    def test_validate_challenge_phases_real_lock_no_error(self, mock_cps):
        mock_cps.return_value.is_valid.return_value = True
        self.phase.refresh_from_db()
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "id": 1,
                    "codename": "pv1",
                    "name": "Phase 1",
                    "description": self.phase_desc_html,
                    "start_date": self.phase.start_date,
                    "end_date": self.phase.end_date,
                }
            ]
        }
        self.util.validate_challenge_phases([1])
        self.assertEqual(self.util.error_messages, [])

    @mockpatch(
        "challenges.challenge_config_utils.ChallengePhaseCreateSerializer"
    )
    def test_validate_challenge_phases_real_lock_error(self, mock_cps):
        mock_cps.return_value.is_valid.return_value = True
        self.phase.refresh_from_db()
        self.util.yaml_file_data = {
            "challenge_phases": [
                {
                    "id": 1,
                    "codename": "pv1",
                    "name": "Renamed Phase",
                    "description": self.phase_desc_html,
                    "start_date": self.phase.start_date,
                    "end_date": self.phase.end_date,
                }
            ]
        }
        self.util.validate_challenge_phases([1])
        self.assertTrue(
            any("approved by an admin" in m for m in self.util.error_messages)
        )

    @mockpatch(
        "challenges.challenge_config_utils.ZipChallengePhaseSplitSerializer"
    )
    def test_validate_challenge_phase_splits_real_lock_no_error(
        self, mock_zss
    ):
        mock_zss.return_value.is_valid.return_value = True
        self.util.yaml_file_data = {
            "challenge_phase_splits": [
                {
                    "is_leaderboard_order_descending": True,
                    "leaderboard_decimal_precision": 2,
                    "visibility": ChallengePhaseSplit.PUBLIC,
                    "dataset_split_id": 1,
                    "leaderboard_id": 1,
                    "challenge_phase_id": 1,
                }
            ]
        }
        self.util.phase_ids = [1]
        self.util.leaderboard_ids = [1]
        self.util.dataset_splits_ids = [1]
        self.util.validate_challenge_phase_splits([(1, 1, 1)], [1], [1], [1])
        self.assertEqual(self.util.error_messages, [])

    @mockpatch(
        "challenges.challenge_config_utils.ZipChallengePhaseSplitSerializer"
    )
    def test_validate_challenge_phase_splits_real_lock_error(self, mock_zss):
        mock_zss.return_value.is_valid.return_value = True
        self.util.yaml_file_data = {
            "challenge_phase_splits": [
                {
                    "is_leaderboard_order_descending": True,
                    "leaderboard_decimal_precision": 2,
                    "visibility": ChallengePhaseSplit.HOST,
                    "dataset_split_id": 1,
                    "leaderboard_id": 1,
                    "challenge_phase_id": 1,
                }
            ]
        }
        self.util.phase_ids = [1]
        self.util.leaderboard_ids = [1]
        self.util.dataset_splits_ids = [1]
        self.util.validate_challenge_phase_splits([(1, 1, 1)], [1], [1], [1])
        self.assertTrue(self.util.error_messages)


@override_settings(MEDIA_ROOT="/tmp/evalai-vcu-orch")
class TestValidateChallengeConfigUtilOrchestratorBranch(TestCase):
    """Cover validate_challenge_config_util() when current_challenge is set."""

    def setUp(self):
        os.makedirs("/tmp/evalai-vcu-orch", exist_ok=True)
        suffix = uuid.uuid4().hex[:12]
        self.user = User.objects.create_user(
            username="orch_{}".format(suffix), password="secret"
        )
        self.team = ChallengeHostTeam.objects.create(
            team_name="Orch Host {}".format(suffix),
            created_by=self.user,
        )
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title="Orch Challenge",
            short_description="s",
            description="d",
            terms_and_conditions="t",
            submission_guidelines="g",
            creator=self.team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            approved_by_admin=False,
        )
        lb = Leaderboard.objects.create(
            config_id=1,
            schema={"labels": ["a"], "default_order_by": "a"},
        )
        ds = DatasetSplit.objects.create(
            config_id=1,
            name="n",
            codename="c",
        )
        phase = ChallengePhase.objects.create(
            name="P",
            description="d",
            leaderboard_public=False,
            is_public=False,
            start_date=now,
            end_date=now + timedelta(days=1),
            challenge=self.challenge,
            config_id=1,
            codename="o1",
            max_submissions_per_day=100,
            max_submissions=100,
            max_submissions_per_month=100,
        )
        ChallengePhaseSplit.objects.create(
            challenge_phase=phase,
            leaderboard=lb,
            dataset_split=ds,
            visibility=ChallengePhaseSplit.PUBLIC,
            leaderboard_decimal_precision=2,
            is_leaderboard_order_descending=True,
        )

    @mockpatch("challenges.challenge_config_utils.read_yaml_file")
    @mockpatch(
        "challenges.challenge_config_utils.get_yaml_files_from_challenge_config"
    )
    def test_orchestrator_passes_existing_config_ids_to_validators(
        self, mock_get_yaml, mock_read_yaml
    ):
        mock_get_yaml.return_value = (1, "challenge_config.yaml", "extracted")
        mock_read_yaml.return_value = {"title": "T"}
        request = Mock()
        request.data = {"GITHUB_REPOSITORY": "a/b"}
        zip_ref = Mock()
        captured = {}

        def capture_lb(util_self, lb_ids):
            captured["leaderboard_ids"] = list(lb_ids)

        def capture_ph(util_self, ph_ids):
            captured["phase_ids"] = list(ph_ids)

        def capture_ds(util_self, ds_ids):
            captured["dataset_ids"] = list(ds_ids)

        def capture_spl(util_self, split_ids, *args, **kwargs):
            captured["split_ids"] = [
                tuple(int(x) for x in t) for t in split_ids
            ]

        noop = Mock()
        with mockpatch.multiple(
            ValidateChallengeConfigUtil,
            validate_challenge_title=noop,
            validate_challenge_logo=noop,
            validate_challenge_description=noop,
            validate_evaluation_details_file=noop,
            validate_terms_and_conditions_file=noop,
            validate_submission_guidelines_file=noop,
            validate_evaluation_script_file=noop,
            validate_dates=noop,
            validate_serializer=noop,
            validate_leaderboards=capture_lb,
            validate_challenge_phases=capture_ph,
            validate_dataset_splits=capture_ds,
            validate_challenge_phase_splits=capture_spl,
            check_tags=noop,
            check_domain=noop,
            check_prizes=noop,
        ):
            validate_challenge_config_util(
                request,
                self.team,
                "/tmp/base",
                "unique",
                zip_ref,
                self.challenge,
            )
        self.assertEqual(captured["leaderboard_ids"], [1])
        self.assertEqual(captured["phase_ids"], [1])
        self.assertEqual(captured["dataset_ids"], [1])
        self.assertEqual(captured["split_ids"], [(1, 1, 1)])
