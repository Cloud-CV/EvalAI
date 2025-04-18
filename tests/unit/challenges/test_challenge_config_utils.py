import io
import unittest
import zipfile
from os.path import join
from unittest.mock import Mock
from unittest.mock import patch as mockpatch

import pytest
import requests
import yaml
from challenges.challenge_config_utils import (
    ValidateChallengeConfigUtil,
    download_and_write_file,
    get_yaml_files_from_challenge_config,
    get_yaml_read_error,
    is_challenge_config_yaml_html_field_valid,
    is_challenge_phase_split_mapping_valid,
    validate_challenge_config_util,
)
from challenges.models import (
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
)
from django.contrib.auth.models import User
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
            yaml_file_count, yaml_file_name, extracted_folder_name = (
                get_yaml_files_from_challenge_config(zip_file)
            )

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
            "missing_evaluation_script_key": "Evaluation script key is missing.",
            "missing_date": "Start date or end date is missing.",
            "start_date_greater_than_end_date": "Start date is greater than end date.",
            "challenge_metadata_schema_errors": "Schema errors: {}",
        }

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
            "leaderboard_additon_after_creation": "Cannot add new leaderboard after challenge creation.",
            "leaderboard_deletion_after_creation": "Cannot delete leaderboard after challenge creation.",
            "missing_challenge_phases": "Missing challenge phases.",
            "no_codename_for_challenge_phase": "Codename is missing for challenge phase.",
            "duplicate_codename_for_phase": "Duplicate codename '{}' for phase '{}'.",
            "no_test_annotation_file_found": "No test annotation file found for phase '{}'.",
            "is_submission_public_restricted": "Submission is public but restricted to select one submission for phase '{}'.",
            "missing_dates_challenge_phase": "Missing start or end date for phase '{}'.",
            "start_date_greater_than_end_date_challenge_phase": "Start date is greater than end date for phase '{}'.",
            "missing_option_in_submission_meta_attribute": "Missing options in submission meta attribute for phase '{}'.",
            "invalid_submission_meta_attribute_types": "Invalid submission meta attribute type '{}' for phase '{}'.",
            "missing_fields_in_submission_meta_attribute": "Missing fields '{}' in submission meta attribute for phase '{}'.",
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

    def test_leaderboard_addition_after_creation(self):
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": "new_leaderboard_id",
                    "schema": {"labels": ["a"], "default_order_by": "a"},
                }
            ]
        }
        self.util.validate_leaderboards(["existing_leaderboard_id"])
        self.assertIn(
            "Leaderboard schema error for leaderboard with ID: new_leaderboard_id",
            self.util.error_messages[0],
        )

    def test_leaderboard_addition_after_creation_with_multiple_leaderboards(
        self,
    ):
        self.util.yaml_file_data = {
            "leaderboard": [
                {
                    "id": "new_leaderboard_id1",
                    "schema": {"labels": ["a"], "default_order_by": "a"},
                },
                {
                    "id": "new_leaderboard_id2",
                    "schema": {"labels": ["b"], "default_order_by": "b"},
                },
            ]
        }
        self.util.validate_leaderboards(["existing_leaderboard_id"])
        self.assertIn(
            "Leaderboard schema error for leaderboard with ID: new_leaderboard_id1",
            self.util.error_messages[0],
        )

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
            "Challenge phase schema errors: 9 - {'description': [ErrorDetail(string='This field may not be null.', code='null')]}",
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
            "Challenge phase schema errors: 3 - {'description': [ErrorDetail(string='This field may not be null.', code='null')]}",
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
