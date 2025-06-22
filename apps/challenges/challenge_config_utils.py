import logging
import re
import zipfile
from os.path import basename, isfile, join

import requests
import yaml
from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
)
from django.core.files.base import ContentFile
from rest_framework import status
from yaml.scanner import ScannerError

from .serializers import (
    ChallengePhaseCreateSerializer,
    DatasetSplitSerializer,
    LeaderboardSerializer,
    ZipChallengePhaseSplitSerializer,
    ZipChallengeSerializer,
)
from .utils import (
    get_file_content,
    get_missing_keys_from_dict,
    read_file_data_as_content_file,
)

logger = logging.getLogger(__name__)


def write_file(output_path, mode, file_content):
    with open(output_path, mode) as file:
        file.write(file_content)


def extract_zip_file(file_path, mode, output_path):
    zip_ref = zipfile.ZipFile(file_path, mode)
    zip_ref.extractall(output_path)
    logger.info("Zip file extracted to {}".format(output_path))
    zip_ref.close()
    return zip_ref


def get_yaml_files_from_challenge_config(zip_ref):
    """
    Arguments:
        zip_ref {zipfile} -- reference to challenge config zip
    Returns:
        yaml_file_count {int} -- number of yaml files in zip file
        yaml_file_name {string} -- name of yaml file in the zip file
        extracted_folder_name {string} -- zip file extraction folder name
    """
    yaml_file_count = 0
    yaml_file_name = None
    extracted_folder_name = None
    for name in zip_ref.namelist():
        if (
            name == "challenge_config.yaml" or name == "challenge_config.yml"
        ) and not name.startswith("__MACOSX"):
            yaml_file_name = name
            extracted_folder_name = yaml_file_name.split(
                basename(yaml_file_name)
            )[0]
            yaml_file_count += 1

    if not yaml_file_count:
        return yaml_file_count, None, None
    return yaml_file_count, yaml_file_name, extracted_folder_name


def read_yaml_file(file_path, mode):
    with open(file_path, mode) as stream:
        yaml_file_data = yaml.safe_load(stream)
    return yaml_file_data


def get_yaml_read_error(exc):
    """
    Arguments:
        exc {Exception} -- Exception object
    Returns:
        error_description {string} -- description of yaml read error
        line_number {int} -- line number of error field in yaml file
        column_number {int} -- column number of error field in yaml file
    """
    error_description = None
    line_number = None
    column_number = None
    # To get the problem description
    if hasattr(exc, "problem"):
        error_description = exc.problem
        # To capitalize the first alphabet of the problem description as
        # default is in lowercase
        error_description = error_description[0:].capitalize()
    # To get the error line and column number
    if hasattr(exc, "problem_mark"):
        mark = exc.problem_mark
        line_number = mark.line + 1
        column_number = mark.column + 1
    return error_description, line_number, column_number


def is_challenge_config_yaml_html_field_valid(
    yaml_file_data, key, base_location
):
    """
    Arguments:
        yaml_file_data {dict} -- challenge config yaml dict
        key {string} -- key of the validation field
        base_location {string} -- path of extracted config zip
    Returns:
        is_valid {boolean} -- flag for field validation is success
        message {string} -- error message if any
    """
    value = join(base_location, yaml_file_data.get(key))
    message = ""
    is_valid = False
    if value:
        if not isfile(value):
            message = "File at path {} not found. Please specify a valid file path".format(
                key
            )
        elif not value.endswith(".html"):
            message = "File {} is not a HTML file. Please specify a valid HTML file".format(
                key
            )
        else:
            is_valid = True
    else:
        message = "ERROR: There is no key for {} in YAML file".format(key)
    return is_valid, message


def is_challenge_phase_config_yaml_html_field_valid(
    yaml_file_data, key, base_location
):
    """
    Arguments:
        yaml_file_data {dict} -- challenge config yaml dict
        key {string} -- key of the validation field
        base_location {string} -- path of extracted config zip
    Returns:
        is_valid {boolean} -- flag for field validation is success
        message {string} -- error message if any
    """
    value = yaml_file_data.get(key)
    message = ""
    is_valid = False
    if value:
        is_valid = True
    else:
        message = " ERROR: There is no key for {} in phase {}.".format(
            key, yaml_file_data["name"]
        )
    return is_valid, message


def download_and_write_file(url, stream, output_path, mode):
    """
    Arguments:
        url {string} -- source file url
        stream {boolean} -- flag for download in stream mode
        output_path {string} -- path to write file
        model {string} -- access mode to write file
    Returns:
        is_success {boolean} -- flag for download and write is success
        message {string} -- error message if any
    """
    is_success = False
    message = None
    try:
        response = requests.get(url, stream=stream)
        try:
            if response and response.status_code == status.HTTP_200_OK:
                write_file(output_path, mode, response.content)
                is_success = True
        except IOError:
            message = (
                "Unable to process the uploaded zip file. " "Please try again!"
            )
    except requests.exceptions.RequestException:
        message = (
            "A server error occured while processing zip file. "
            "Please try again!"
        )
    return is_success, message


def is_challenge_phase_split_mapping_valid(
    phase_ids,
    leaderboard_ids,
    dataset_split_ids,
    phase_split,
    challenge_phase_split_index,
):
    """
    Arguments:
        phase_ids {array} -- list of phase ids
        leaderboard_ids {array} -- list of leaderboard ids
        dataset_split_ids {array} -- list of dataset split ids
        phase_split {dict} -- challenge phase split config
    Returns:
        is_success {boolean} -- flag for validation success
    """
    phase_id = phase_split["challenge_phase_id"]
    leaderboard_id = phase_split["leaderboard_id"]
    dataset_split_id = phase_split["dataset_split_id"]
    error_messages = []

    if leaderboard_id not in leaderboard_ids:
        error_messages.append(
            "ERROR: Invalid leaderboard id {} found in challenge phase split {}.".format(
                leaderboard_id, challenge_phase_split_index
            )
        )
    if phase_id not in phase_ids:
        error_messages.append(
            "ERROR: Invalid phased id {} found in challenge phase split {}.".format(
                phase_id, challenge_phase_split_index
            )
        )
    if dataset_split_id not in dataset_split_ids:
        error_messages.append(
            "ERROR: Invalid dataset split id {} found in challenge phase split {}.".format(
                dataset_split_id, challenge_phase_split_index
            )
        )

    if error_messages:
        return False, error_messages
    else:
        return True, error_messages


def get_value_from_field(data, base_location, field_name):
    file_path = join(base_location, data.get(field_name))
    field_value = None
    if file_path.endswith(".html") and isfile(file_path):
        field_value = get_file_content(file_path, "rb").decode("utf-8")
    return field_value


error_message_dict = {
    "no_yaml_file": "There is no YAML file in the zip file you uploaded!",
    "multiple_yaml_files": "There are {} challenge config YAML files instead of 1 in the zip file!",
    "yaml_file_read_error": "\n{} in line {}, column {}\n",
    "missing_challenge_title": "Please add the challenge title",
    "missing_challenge_description": "Please add the challenge description",
    "missing_evaluation_details": "Please add the evaluation details",
    "missing_terms_and_conditions": "Please add the terms and conditions.",
    "missing_submission_guidelines": "Please add the submission guidelines.",
    "missing_evaluation_script": "ERROR: No evaluation script is present in the zip file. Please add it and then try again!",
    "missing_evaluation_script_key": "ERROR: There is no key for the evaluation script in the YAML file. Please add it and then try again!",
    "missing_leaderboard_id": "ERROR: There is no leaderboard ID for the leaderboard.",
    "missing_leaderboard_schema": "ERROR: There is no leaderboard schema for the leaderboard with ID: {}.",
    "missing_leaderboard_default_order_by": "ERROR: There is no 'default_order_by' key in the schema for the leaderboard with ID: {}.",
    "missing_leaderboard_key": "ERROR: There is no key for the leaderboard in the YAML file. Please add it and then try again!",
    "incorrect_default_order_by": "ERROR: The 'default_order_by' value '{}' in the schema for the leaderboard with ID: {} is not a valid label.",
    "leaderboard_schema_error": "ERROR: The leaderboard with ID: {} has the following schema errors:\n {}",
    "leaderboard_additon_after_creation": "ERROR: The leaderboard with ID: {} doesn't exist. Addition of a new leaderboard after challenge creation is not allowed.",
    "leaderboard_deletion_after_creation": "ERROR: The leaderboard with ID: {} not found in config. Deletion of an existing leaderboard after challenge creation is not allowed.",
    "missing_leaderboard_labels": "ERROR: There is no 'labels' key in the schema for the leaderboard with ID: {}.",
    "missing_challenge_phases": "ERROR: No challenge phase key found. Please add challenge phases in the YAML file and try again!",
    "missing_challenge_phase_codename": "ERROR: No codename found for the challenge phase. Please add the codename and try again!",
    "missing_test_annotation_file": "ERROR: No test annotation file found in the zip file for challenge phase {}.",
    "missing_submission_meta_attribute_keys": "ERROR: Please enter the following keys to the submission meta attribute in challenge phase {}: {}",
    "invalid_submission_meta_attribute_types": "ERROR: Please ensure that the submission meta attribute types for the attribute '{}' in challenge phase {} are among the following: boolean, text, radio, or checkbox.",
    "missing_challenge_phase_id": "ERROR: Challenge phase {} doesn't exist. Addition of a new challenge phase after challenge creation is not allowed.",
    "missing_challenge_phase_id_config": "ERROR: Challenge phase {} doesn't exist. Addition of a new challenge phase after challenge creation is not allowed.",
    "missing_leaderboard_id_config": "ERROR: The leaderboard with ID: {} doesn't exist. Addition of a new leaderboard after challenge creation is not allowed.",
    "missing_existing_leaderboard_id": "ERROR: The leaderboard with ID: {} was not found in the configuration. Deletion of an existing leaderboard after challenge creation is not allowed.",
    "missing_existing_challenge_phase_id": "ERROR: Challenge phase {} was not found in the configuration. Deletion of an existing challenge phase after challenge creation is not allowed.",
    "missing_dataset_splits_key": "ERROR: There is no key for dataset splits.",
    "missing_dataset_split_name": "ERROR: There is no name for dataset split {}.",
    "missing_dataset_split_codename": "ERROR: There is no codename for dataset split {}.",
    "duplicate_dataset_split_codename": "ERROR: Duplicate codename {} for dataset split {}. Please ensure codenames are unique.",
    "dataset_split_schema_errors": "ERROR: Dataset split {} has the following schema errors:\n {}",
    "dataset_split_addition": "ERROR: Dataset split {} doesn't exist. Addition of a new dataset split after challenge creation is not allowed.",
    "missing_existing_dataset_split_id": "ERROR: Dataset split {} not found in config. Deletion of existing dataset split after challenge creation is not allowed.",
    "challenge_phase_split_schema_errors": "ERROR: Challenge phase split {} has the following schema errors:\n {}",
    "missing_keys_in_challenge_phase_splits": "ERROR: The following keys are missing in the challenge phase splits of YAML file (phase_split: {}): {}",
    "no_key_for_challenge_phase_splits": "ERROR: There is no key for challenge phase splits.",
    "no_codename_for_challenge_phase": "ERROR: No codename found for the challenge phase. Please add a codename and try again!",
    "duplicate_codename_for_phase": "ERROR: Duplicate codename {} for phase {}. Please ensure codenames are unique",
    "no_test_annotation_file_found": "ERROR: No test annotation file found in the zip file for challenge phase {}",
    "submission_meta_attribute_option_missing": "ERROR: Please include at least one option in the attribute for challenge phase {}",
    "missing_submission_meta_attribute_fields": "ERROR: Please enter the following fields for the submission meta attribute in challenge phase {}: {}",
    "challenge_phase_schema_errors": "ERROR: Challenge phase {} has the following schema errors:\n {}",
    "is_submission_public_restricted": "ERROR: is_submission_public can't be 'True' for challenge phase '{}' with is_restricted_to_select_one_submission 'True'. Please change is_submission_public to 'False' and try again!",
    "missing_option_in_submission_meta_attribute": "ERROR: Please include at least one option in the attribute for challenge phase {}",
    "missing_fields_in_submission_meta_attribute": "ERROR: Please enter the following fields for the submission meta attribute in challenge phase {}: {}",
    "missing_date": "ERROR: Please add the start_date and end_date.",
    "start_date_greater_than_end_date": "ERROR: Start date cannot be greater than end date.",
    "missing_dates_challenge_phase": "ERROR: Please add the start_date and end_date in challenge phase {}.",
    "start_date_greater_than_end_date_challenge_phase": "ERROR: Start date cannot be greater than end date in challenge phase {}.",
    "extra_tags": "ERROR: Tags are limited to 4. Please remove extra tags then try again!",
    "wrong_domain": "ERROR: Domain name is incorrect. Please enter correct domain name then try again!",
    "duplicate_combinations_in_challenge_phase_splits": "ERROR: Duplicate combinations of leaderboard_id {}, challenge_phase_id {} and dataset_split_id {} found in challenge phase splits.",
    "sponsor_not_found": "ERROR: Sponsor name or url not found in YAML data.",
    "prize_not_found": "ERROR: Prize rank or amount not found in YAML data.",
    "duplicate_rank": "ERROR: Duplicate rank {} found in YAML data.",
    "prize_amount_wrong": "ERROR: Invalid amount value {}. Amount should be in decimal format with three-letter currency code (e.g. 100.00USD, 500EUR, 1000INR).",
    "prize_rank_wrong": "ERROR: Invalid rank value {}. Rank should be an integer.",
    "challenge_metadata_schema_errors": "ERROR: Unable to serialize the challenge because of the following errors: {}.",
    "evaluation_script_not_zip": "ERROR: Please pass in a zip file as evaluation script. If using the `evaluation_script` directory (recommended), it should be `evaluation_script.zip`.",
    "docker_based_challenge": "ERROR: New Docker based challenges are not supported starting March 15, 2025.",
}


class ValidateChallengeConfigUtil:
    def __init__(
        self,
        request,
        challenge_host_team,
        base_location,
        unique_folder_name,
        zip_ref,
        current_challenge,
    ):
        """
        Class containing methods to validate the challenge configuration

        Arguments:
            request {HttpRequest} -- The request object
            challenge_host_team {int} -- the team creating the challenge
            base_location {str} -- The temp base directory for storing all the files and folders while validating the zip file
            unique_folder_name {str} -- name of the challenge zip file and the parent dir of extracted folder
            zip_ref {zipfile.ZipFile} -- reference to challenge config zip
            current_challenge {apps.challenges.models.Challenge} - the existing challenge for the github repo, if any
        """
        self.request = request
        self.challenge_host_team = challenge_host_team
        self.base_location = base_location
        self.unique_folder_name = unique_folder_name
        self.zip_ref = zip_ref
        self.current_challenge = current_challenge

        self.error_messages = []
        self.files = {}
        self.yaml_file_data = None
        self.error_messages_dict = error_message_dict

        (
            self.yaml_file_count,
            self.yaml_file,
            self.extracted_folder_name,
        ) = get_yaml_files_from_challenge_config(self.zip_ref)

        self.valid_yaml = self.read_and_validate_yaml()
        if self.valid_yaml:
            self.challenge_config_location = join(
                self.base_location,
                self.unique_folder_name,
                self.extracted_folder_name,
            )
        self.phase_ids = []
        self.leaderboard_ids = []

    def read_and_validate_yaml(self):
        if not self.yaml_file_count:
            message = self.error_messages_dict.get("no_yaml_file")
            self.error_messages.append(message)
            return False

        if self.yaml_file_count > 1:
            message = self.error_messages_dict.get(
                "multiple_yaml_files"
            ).format(self.yaml_file_count)
            self.error_messages.append(message)
            return False

        # YAML Read Error
        try:
            self.yaml_file_path = join(
                self.base_location, self.unique_folder_name, self.yaml_file
            )
            self.yaml_file_data = read_yaml_file(self.yaml_file_path, "r")
            return True
        except (yaml.YAMLError, ScannerError) as exc:
            (
                error_description,
                line_number,
                column_number,
            ) = get_yaml_read_error(exc)
            message = self.error_messages_dict.get(
                "yaml_file_read_error"
            ).format(error_description, line_number, column_number)
            self.error_messages.append(message)
            return False

    def validate_challenge_title(self):
        challenge_title = self.yaml_file_data.get("title")
        if not challenge_title or len(challenge_title) == 0:
            message = self.error_messages_dict.get("missing_challenge_title")
            self.error_messages.append(message)

    def validate_challenge_logo(self):
        image = self.yaml_file_data.get("image")
        if image and (
            image.endswith(".jpg")
            or image.endswith(".jpeg")
            or image.endswith(".png")
        ):
            self.challenge_image_path = join(
                self.base_location,
                self.unique_folder_name,
                self.extracted_folder_name,
                image,
            )

            if isfile(self.challenge_image_path):
                self.challenge_image_file = ContentFile(
                    get_file_content(self.challenge_image_path, "rb"), image
                )
            else:
                self.challenge_image_file = None
        else:
            self.challenge_image_file = None
        self.files["challenge_image_file"] = self.challenge_image_file

    def validate_challenge_description(self):
        challenge_description = self.yaml_file_data.get("description")
        if not challenge_description or len(challenge_description) == 0:
            message = self.error_messages_dict.get(
                "missing_challenge_description"
            )
            self.error_messages.append(message)
        else:
            is_valid, message = is_challenge_config_yaml_html_field_valid(
                self.yaml_file_data,
                "description",
                self.challenge_config_location,
            )
            if not is_valid:
                self.error_messages.append(message)
            else:
                self.yaml_file_data["description"] = get_value_from_field(
                    self.yaml_file_data,
                    self.challenge_config_location,
                    "description",
                )

    # Check for evaluation details file
    def validate_evaluation_details_file(self):
        evaluation_details = self.yaml_file_data.get("evaluation_details")
        if not evaluation_details or len(evaluation_details) == 0:
            message = self.error_messages_dict.get(
                "missing_evaluation_details"
            )
            self.error_messages.append(message)
        else:
            is_valid, message = is_challenge_config_yaml_html_field_valid(
                self.yaml_file_data,
                "evaluation_details",
                self.challenge_config_location,
            )
            if not is_valid:
                self.error_messages.append(message)
            else:
                self.yaml_file_data["evaluation_details"] = (
                    get_value_from_field(
                        self.yaml_file_data,
                        self.challenge_config_location,
                        "evaluation_details",
                    )
                )

    # Validate terms and conditions file
    def validate_terms_and_conditions_file(self):
        terms_and_conditions = self.yaml_file_data.get("terms_and_conditions")
        if not terms_and_conditions or len(terms_and_conditions) == 0:
            message = self.error_messages_dict.get(
                "missing_terms_and_conditions"
            )
            self.error_messages.append(message)
        else:
            is_valid, message = is_challenge_config_yaml_html_field_valid(
                self.yaml_file_data,
                "terms_and_conditions",
                self.challenge_config_location,
            )
            if not is_valid:
                self.error_messages.append(message)
            else:
                self.yaml_file_data["terms_and_conditions"] = (
                    get_value_from_field(
                        self.yaml_file_data,
                        self.challenge_config_location,
                        "terms_and_conditions",
                    )
                )

    # Validate  ubmission guidelines file
    def validate_submission_guidelines_file(self):
        submission_guidelines = self.yaml_file_data.get(
            "submission_guidelines"
        )
        if not submission_guidelines or len(submission_guidelines) == 0:
            message = self.error_messages_dict.get(
                "missing_submission_guidelines"
            )
            self.error_messages.append(message)
        else:
            is_valid, message = is_challenge_config_yaml_html_field_valid(
                self.yaml_file_data,
                "submission_guidelines",
                self.challenge_config_location,
            )
            if not is_valid:
                self.error_messages.append(message)
            else:
                self.yaml_file_data["submission_guidelines"] = (
                    get_value_from_field(
                        self.yaml_file_data,
                        self.challenge_config_location,
                        "submission_guidelines",
                    )
                )

    def validate_evaluation_script_file(self):
        evaluation_script = self.yaml_file_data.get("evaluation_script")
        if evaluation_script:
            if not evaluation_script.endswith(".zip"):
                message = self.error_messages_dict.get(
                    "evaluation_script_not_zip"
                )
                self.error_messages.append(message)
            else:
                evaluation_script_path = join(
                    self.challenge_config_location, evaluation_script
                )
                # Check for evaluation script file in extracted zip folder
                if isfile(evaluation_script_path):
                    self.challenge_evaluation_script_file = (
                        read_file_data_as_content_file(
                            evaluation_script_path,
                            "rb",
                            evaluation_script_path,
                        )
                    )
                    self.files["challenge_evaluation_script_file"] = (
                        self.challenge_evaluation_script_file
                    )
                else:
                    message = self.error_messages_dict.get(
                        "missing_evaluation_script"
                    )
                    self.error_messages.append(message)
        else:
            message = self.error_messages_dict.get(
                "missing_evaluation_script_key"
            )
            self.error_messages.append(message)

    def validate_dates(self):
        start_date = self.yaml_file_data.get("start_date")
        end_date = self.yaml_file_data.get("end_date")

        if not start_date or not end_date:
            message = self.error_messages_dict.get("missing_date")
            self.error_messages.append(message)
        if start_date and end_date:
            if start_date > end_date:
                message = self.error_messages_dict.get(
                    "start_date_greater_than_end_date"
                )
                self.error_messages.append(message)

    def validate_serializer(self):
        if not len(self.error_messages):
            serializer = ZipChallengeSerializer(
                data=self.yaml_file_data,
                context={
                    "request": self.request,
                    "challenge_host_team": self.challenge_host_team,
                    "image": self.challenge_image_file,
                    "evaluation_script": self.challenge_evaluation_script_file,
                    "github_repository": self.request.data[
                        "GITHUB_REPOSITORY"
                    ],
                },
            )
            if not serializer.is_valid():
                message = self.error_messages_dict[
                    "challenge_metadata_schema_errors"
                ].format(str(serializer.errors))
                self.error_messages.append(message)

    # Check for leaderboards
    def validate_leaderboards(self, current_leaderboard_config_ids):
        leaderboard = self.yaml_file_data.get("leaderboard")
        if leaderboard:
            for data in leaderboard:
                error = False
                if "id" not in data:
                    message = self.error_messages_dict.get(
                        "missing_leaderboard_id"
                    )
                    self.error_messages.append(message)
                    error = True
                if "schema" not in data:
                    message = self.error_messages_dict.get(
                        "missing_leaderboard_schema"
                    ).format(data.get("id"))
                    self.error_messages.append(message)
                    error = True
                else:
                    if "labels" not in data["schema"]:
                        message = self.error_messages_dict.get(
                            "missing_leaderboard_labels"
                        ).format(data.get("id"))
                        self.error_messages.append(message)
                        error = True
                    if "default_order_by" not in data["schema"]:
                        message = self.error_messages_dict.get(
                            "missing_leaderboard_default_order_by"
                        ).format(data.get("id"))
                        self.error_messages.append(message)
                        error = True
                    else:
                        default_order_by = data["schema"]["default_order_by"]
                        if (
                            "labels" in data["schema"]
                            and default_order_by
                            not in data["schema"]["labels"]
                        ):
                            message = self.error_messages_dict.get(
                                "incorrect_default_order_by"
                            ).format(default_order_by, data.get("id"))
                            self.error_messages.append(message)
                            error = True
                if not error:
                    serializer = LeaderboardSerializer(
                        data=data, context={"config_id": data["id"]}
                    )
                    if not serializer.is_valid():
                        serializer_error = str(serializer.errors)
                        message = self.error_messages_dict.get(
                            "leaderboard_schema_error"
                        ).format(data["id"], serializer_error)
                        self.error_messages.append(message)
                    else:
                        if (
                            current_leaderboard_config_ids
                            and int(data["id"])
                            not in current_leaderboard_config_ids
                        ):
                            message = self.error_messages_dict.get(
                                "leaderboard_additon_after_creation"
                            ).format(data["id"])
                            self.error_messages.append(message)
                        self.leaderboard_ids.append(data["id"])
        else:
            message = self.error_messages_dict.get("missing_leaderboard_key")
            self.error_messages.append(message)

        for current_leaderboard_id in current_leaderboard_config_ids:
            if current_leaderboard_id not in self.leaderboard_ids:
                message = self.error_messages_dict.get(
                    "leaderboard_deletion_after_creation"
                ).format(current_leaderboard_id)
                self.error_messages.append(message)

    # Check for challenge phases
    def validate_challenge_phases(self, current_phase_config_ids):
        challenge_phases_data = self.yaml_file_data.get("challenge_phases")
        if not challenge_phases_data:
            message = self.error_messages_dict["missing_challenge_phases"]
            self.error_messages.append(message)
            return self.error_messages, self.yaml_file_data, self.files

        self.phase_ids = []
        phase_codenames = []
        self.files["challenge_test_annotation_files"] = []
        for data in challenge_phases_data:
            if "codename" not in data:
                self.error_messages.append(
                    self.error_messages_dict["no_codename_for_challenge_phase"]
                )
            else:
                if data["codename"] not in phase_codenames:
                    phase_codenames.append(data["codename"])
                else:
                    message = self.error_messages_dict[
                        "duplicate_codename_for_phase"
                    ].format(data["codename"], data["name"])
                    self.error_messages.append(message)
            test_annotation_file = data.get("test_annotation_file")
            if test_annotation_file:
                test_annotation_file_path = join(
                    self.challenge_config_location, test_annotation_file
                )
                if isfile(test_annotation_file_path):
                    challenge_test_annotation_file = (
                        read_file_data_as_content_file(
                            test_annotation_file_path,
                            "rb",
                            test_annotation_file_path,
                        )
                    )
                    self.files["challenge_test_annotation_files"].append(
                        challenge_test_annotation_file
                    )
                else:
                    message = self.error_messages_dict[
                        "no_test_annotation_file_found"
                    ].format(data["name"])
                    self.error_messages.append(message)
            else:
                test_annotation_file_path = None
                self.files["challenge_test_annotation_files"].append(None)

            if data.get("max_submissions_per_month", None) is None:
                data["max_submissions_per_month"] = data.get(
                    "max_submissions", None
                )

            (
                is_valid,
                message,
            ) = is_challenge_phase_config_yaml_html_field_valid(
                data, "description", self.challenge_config_location
            )
            if not is_valid:
                self.error_messages.append(message)
            else:
                data["description"] = get_value_from_field(
                    data, self.challenge_config_location, "description"
                )

            if data.get("is_submission_public") and data.get(
                "is_restricted_to_select_one_submission"
            ):
                message = self.error_messages_dict[
                    "is_submission_public_restricted"
                ].format(data["name"])
                self.error_messages.append(message)

            start_date = data.get("start_date")
            end_date = data.get("end_date")
            if not start_date or not end_date:
                message = self.error_messages_dict.get(
                    "missing_dates_challenge_phase"
                ).format(data.get("id"))
                self.error_messages.append(message)
            if start_date and end_date:
                if start_date > end_date:
                    message = self.error_messages_dict.get(
                        "start_date_greater_than_end_date_challenge_phase"
                    ).format(data.get("id"))
                    self.error_messages.append(message)

            # To ensure that the schema for submission meta attributes is valid
            if data.get("submission_meta_attributes"):
                for attribute in data["submission_meta_attributes"]:
                    keys = ["name", "description", "type"]
                    missing_keys = get_missing_keys_from_dict(attribute, keys)

                    if len(missing_keys) == 0:
                        valid_attribute_types = [
                            "boolean",
                            "text",
                            "radio",
                            "checkbox",
                        ]
                        attribute_type = attribute["type"]
                        if attribute_type in valid_attribute_types:
                            if (
                                attribute_type == "radio"
                                or attribute_type == "checkbox"
                            ):
                                options = attribute.get("options")
                                if not options or not len(options):
                                    message = self.error_messages_dict[
                                        "missing_option_in_submission_meta_attribute"
                                    ].format(data["id"])
                                    self.error_messages.append(message)
                        else:
                            message = self.error_messages_dict[
                                "invalid_submission_meta_attribute_types"
                            ].format(attribute_type, data["id"])
                            self.error_messages.append(message)
                    else:
                        missing_keys_string = ", ".join(missing_keys)
                        message = self.error_messages_dict[
                            "missing_fields_in_submission_meta_attribute"
                        ].format(data["id"], missing_keys_string)
                        self.error_messages.append(message)

            if test_annotation_file_path is not None and isfile(
                test_annotation_file_path
            ):
                serializer = ChallengePhaseCreateSerializer(
                    data=data,
                    context={
                        "exclude_fields": ["challenge"],
                        "test_annotation": challenge_test_annotation_file,
                        "config_id": data["id"],
                    },
                )
            else:
                serializer = ChallengePhaseCreateSerializer(
                    data=data,
                    context={
                        "exclude_fields": ["challenge"],
                        "config_id": data["id"],
                    },
                )
            if not serializer.is_valid():
                serializer_error = str(serializer.errors)
                message = self.error_messages_dict[
                    "challenge_phase_schema_errors"
                ].format(data["id"], serializer_error)
                self.error_messages.append(message)
            else:
                self.phase_ids.append(data["id"])

    def validate_challenge_phase_splits(self, current_phase_split_ids):
        challenge_phase_splits = self.yaml_file_data.get(
            "challenge_phase_splits"
        )
        challenge_phase_split_set = set()
        duplicates_found = False
        total_duplicates = []
        for data in challenge_phase_splits:
            combination = (
                data["leaderboard_id"],
                data["challenge_phase_id"],
                data["dataset_split_id"],
            )
            if combination in challenge_phase_split_set:
                duplicates_found = True
                total_duplicates += [combination]
            else:
                challenge_phase_split_set.add(combination)

        if duplicates_found:
            message = self.error_messages_dict[
                "duplicate_combinations_in_challenge_phase_splits"
            ]
            self.error_messages.append(message)
            for combination in total_duplicates:
                message = self.error_messages_dict[
                    "duplicate_combinations_in_challenge_phase_splits"
                ].format(combination[0], combination[1], combination[2])
                self.error_messages.append(message)

        if challenge_phase_splits:
            phase_split = 1
            exclude_fields = [
                "challenge_phase",
                "dataset_split",
                "leaderboard",
            ]
            for data in challenge_phase_splits:
                expected_keys = {
                    "is_leaderboard_order_descending",
                    "leaderboard_decimal_precision",
                    "visibility",
                    "dataset_split_id",
                    "leaderboard_id",
                    "challenge_phase_id",
                }
                combination = (
                    data["leaderboard_id"],
                    data["challenge_phase_id"],
                    data["dataset_split_id"],
                )
                if expected_keys.issubset(data.keys()):
                    if combination in current_phase_split_ids:
                        current_phase_split_ids.remove(combination)
                    (
                        _is_mapping_valid,
                        messages,
                    ) = is_challenge_phase_split_mapping_valid(
                        self.phase_ids,
                        self.leaderboard_ids,
                        self.dataset_splits_ids,
                        data,
                        phase_split,
                    )
                    self.error_messages += messages
                    serializer = ZipChallengePhaseSplitSerializer(
                        data=data, context={"exclude_fields": exclude_fields}
                    )
                    if not serializer.is_valid():
                        serializer_error = str(serializer.errors)
                        message = self.error_messages_dict[
                            "challenge_phase_split_schema_errors"
                        ].format(phase_split, serializer_error)
                        self.error_messages.append(message)
                    phase_split += 1
                else:
                    missing_keys = expected_keys - data.keys()
                    missing_keys_string = ", ".join(missing_keys)
                    message = self.error_messages_dict[
                        "missing_keys_in_challenge_phase_splits"
                    ].format(phase_split, missing_keys_string)
                    self.error_messages.append(message)
        else:
            message = self.error_messages_dict[
                "no_key_for_challenge_phase_splits"
            ]
            self.error_messages.append(message)

    # Check for dataset splits
    def validate_dataset_splits(self, current_dataset_config_ids):
        dataset_splits = self.yaml_file_data.get("dataset_splits")
        dataset_split_codenames = []
        self.dataset_splits_ids = []
        if dataset_splits:
            for split in dataset_splits:
                name = split.get("name")
                if not name:
                    message = self.error_messages_dict[
                        "missing_dataset_split_name"
                    ].format(split.get("id"))
                    self.error_messages.append(message)
                if "codename" not in split:
                    message = self.error_messages_dict[
                        "missing_dataset_split_codename"
                    ].format(split.get("id"))
                    self.error_messages.append(message)
                else:
                    if split["codename"] not in dataset_split_codenames:
                        dataset_split_codenames.append(split["codename"])
                    else:
                        message = self.error_messages_dict[
                            "duplicate_dataset_split_codename"
                        ].format(split["codename"], split["name"])
                        self.error_messages.append(message)
            for split in dataset_splits:
                serializer = DatasetSplitSerializer(
                    data=split, context={"config_id": split["id"]}
                )
                if not serializer.is_valid():
                    serializer_error = str(serializer.errors)
                    message = self.error_messages_dict[
                        "dataset_split_schema_errors"
                    ].format(split["id"], serializer_error)
                    self.error_messages.append(message)
                else:
                    self.dataset_splits_ids.append(split["id"])
        else:
            message = self.error_messages_dict["missing_dataset_splits_key"]
            self.error_messages.append(message)

        for current_dataset_split_config_id in current_dataset_config_ids:
            if current_dataset_split_config_id not in self.dataset_splits_ids:
                message = self.error_messages_dict[
                    "missing_existing_dataset_split_id"
                ].format(current_dataset_split_config_id)
                self.error_messages.append(message)

    # Check for Tags and Domain
    def check_tags(self):
        if "tags" in self.yaml_file_data:
            tags_data = self.yaml_file_data["tags"]
            # Verify Tags are limited to 4
            if len(tags_data) > 4:
                message = self.error_messages_dict["extra_tags"]
                self.error_messages.append(message)

    def check_domain(self):
        # Verify Domain name is correct
        if "domain" in self.yaml_file_data:
            domain_value = self.yaml_file_data["domain"]
            domain_choice = [option[0] for option in Challenge.DOMAIN_OPTIONS]
            if domain_value not in domain_choice:
                message = self.error_messages_dict["wrong_domain"]
                self.error_messages.append(message)

    def check_sponsor(self):
        # Verify Sponsor is correct
        if "sponsors" in self.yaml_file_data:
            for sponsor in self.yaml_file_data["sponsors"]:
                if "name" not in sponsor or "website" not in sponsor:
                    message = self.error_messages_dict["sponsor_not_found"]
                    self.error_messages.append(message)

    def check_prizes(self):
        # Verify Prizes are correct
        if "prizes" in self.yaml_file_data:
            rank_set = set()
            for prize in self.yaml_file_data["prizes"]:
                if "rank" not in prize or "amount" not in prize:
                    message = self.error_messages_dict["prize_not_found"]
                    self.error_messages.append(message)
                # Check for duplicate rank.
                rank = prize["rank"]
                if rank in rank_set:
                    message = self.error_messages_dict[
                        "duplicate_rank"
                    ].format(rank)
                    self.error_messages.append(message)
                rank_set.add(rank)
                if not isinstance(rank, int) or rank < 1:
                    message = self.error_messages_dict[
                        "prize_rank_wrong"
                    ].format(rank)
                    self.error_messages.append(message)
                if not re.match(r"^\d+(\.\d{1,2})?[A-Z]{3}$", prize["amount"]):
                    message = self.error_messages_dict[
                        "prize_amount_wrong"
                    ].format(prize["amount"])
                    self.error_messages.append(message)

    def check_docker_based_challenge(self):
        if "is_docker_based" in self.yaml_file_data:
            if self.yaml_file_data["is_docker_based"]:
                message = self.error_messages_dict["docker_based_challenge"]
                self.error_messages.append(message)


def validate_challenge_config_util(
    request,
    challenge_host_team,
    BASE_LOCATION,
    unique_folder_name,
    zip_ref,
    current_challenge,
):
    """
    Function to validate a challenge config

    Arguments:
        request {HttpRequest} -- The request object
        BASE_LOCATION {str} -- The temp base directory for storing all the files and folders while validating the zip file
        unique_folder_name {str} -- name of the challenge zip file and the parent dir of extracted folder
        zip_ref {zipfile.ZipFile} -- reference to challenge config zip
        current_challenge {apps.challenges.models.Challenge} - the existing challenge for the github repo, if any
    """

    val_config_util = ValidateChallengeConfigUtil(
        request,
        challenge_host_team,
        BASE_LOCATION,
        unique_folder_name,
        zip_ref,
        current_challenge,
    )
    if not val_config_util.valid_yaml:
        return (
            val_config_util.error_messages,
            val_config_util.yaml_file_data,
            val_config_util.files,
        )

    # # Validate challenge title
    val_config_util.validate_challenge_title()

    # Validate challenge logo
    val_config_util.validate_challenge_logo()

    # Validate challenge description
    val_config_util.validate_challenge_description()

    # Validate evaluation details
    val_config_util.validate_evaluation_details_file()

    # Validate terms and conditions
    val_config_util.validate_terms_and_conditions_file()

    # Validate submission guidelines
    val_config_util.validate_submission_guidelines_file()

    # Validate evaluation script
    val_config_util.validate_evaluation_script_file()

    val_config_util.validate_dates()

    val_config_util.validate_serializer()

    # Get existing config IDs for leaderboards and dataset splits
    if current_challenge:
        current_challenge_phases = ChallengePhase.objects.filter(
            challenge=current_challenge.id
        )
        current_challenge_phase_splits = ChallengePhaseSplit.objects.filter(
            challenge_phase__in=current_challenge_phases
        )
        current_leaderboards = Leaderboard.objects.filter(
            id__in=current_challenge_phase_splits.values("leaderboard")
        )
        current_dataset_splits = DatasetSplit.objects.filter(
            id__in=current_challenge_phase_splits.values("dataset_split")
        )

        current_leaderboard_config_ids = [
            int(x.config_id) for x in current_leaderboards
        ]
        current_dataset_config_ids = [
            int(x.config_id) for x in current_dataset_splits
        ]
        current_phase_config_ids = [
            int(x.config_id) for x in current_challenge_phases
        ]
        current_phase_split_ids = [
            (
                split.leaderboard.config_id,
                split.challenge_phase.config_id,
                split.dataset_split.config_id,
            )
            for split in current_challenge_phase_splits
        ]
    else:
        current_leaderboard_config_ids = []
        current_dataset_config_ids = []
        current_phase_config_ids = []
        current_phase_split_ids = []

    # Validate leaderboards
    val_config_util.validate_leaderboards(current_leaderboard_config_ids)

    # Validate challenge phases
    val_config_util.validate_challenge_phases(current_phase_config_ids)

    # Validate dataset splits
    val_config_util.validate_dataset_splits(current_dataset_config_ids)

    # Validate challenge phase splits
    val_config_util.validate_challenge_phase_splits(current_phase_split_ids)

    # Validate tags
    val_config_util.check_tags()

    # Validate domain
    val_config_util.check_domain()
    # Check for Sponsor
    # val_config_util.check_sponsor()

    # Check for Prize
    val_config_util.check_prizes()

    # Check for Docker based challenge
    val_config_util.check_docker_based_challenge()

    return (
        val_config_util.error_messages,
        val_config_util.yaml_file_data,
        val_config_util.files,
    )
