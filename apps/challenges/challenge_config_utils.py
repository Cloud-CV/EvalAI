import logging
import requests
import zipfile
import yaml

from django.core.files.base import ContentFile

from os.path import basename, isfile, join
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
        if (name.endswith(".yaml") or name.endswith(".yml")) and (
            not name.startswith("__MACOSX")
        ):
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
        # To capitalize the first alphabet of the problem description as default is in lowercase
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
    value = yaml_file_data.get(key)
    message = ""
    is_valid = False
    if value:
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
    phase_ids, leaderboard_ids, dataset_split_ids, phase_split
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
    if phase_id in phase_ids:
        if leaderboard_id in leaderboard_ids:
            if dataset_split_id in dataset_split_ids:
                return True
            else:
                return False
        else:
            return False
    return False


def get_value_from_field(data, base_location, field_name):
    file_path = join(base_location, data.get(field_name))
    field_value = None
    if file_path.endswith(".html") and isfile(file_path):
        field_value = get_file_content(file_path, "rb").decode("utf-8")
    return field_value


def validate_challenge_config_util(
    request, challenge_host_team, BASE_LOCATION, unique_folder_name, zip_ref
):
    """
    Function to validate a challenge config

    Arguments:
        request {HttpRequest} -- The request object
        BASE_LOCATION {str} -- The temp base directory for storing all the files and folders while validating the zip file
        unique_folder_name {str} -- name of the challenge zip file and the parent dir of extracted folder
        zip_ref {zipfile.ZipFile} -- reference to challenge config zip
    """

    error_messages = []
    files = {}
    yaml_file_data = None

    (
        yaml_file_count,
        yaml_file,
        extracted_folder_name,
    ) = get_yaml_files_from_challenge_config(zip_ref)

    if not yaml_file_count:
        message = "There is no YAML file in zip file you uploaded!"
        error_messages.append(message)
        return error_messages, yaml_file_data, files

    if yaml_file_count > 1:
        message = (
            "There are {0} YAML files instead of one in zip file!".format(
                yaml_file_count
            )
        )
        error_messages.append(message)
        return error_messages, yaml_file_data, files

    try:
        yaml_file_path = join(BASE_LOCATION, unique_folder_name, yaml_file)
        yaml_file_data = read_yaml_file(yaml_file_path, "r")
    except (yaml.YAMLError, ScannerError) as exc:
        error_description, line_number, column_number = get_yaml_read_error(
            exc
        )
        message = "\n{} in line {}, column {}\n".format(
            error_description, line_number, column_number
        )
        error_messages.append(message)
        return error_messages, yaml_file_data, files

    # Check for challenge title
    challenge_title = yaml_file_data.get("title")
    if not challenge_title or len(challenge_title) == 0:
        message = "Please add the challenge title"
        error_messages.append(message)

    # Check for the challenge logo
    image = yaml_file_data.get("image")
    if image and (
        image.endswith(".jpg")
        or image.endswith(".jpeg")
        or image.endswith(".png")
    ):
        challenge_image_path = join(
            BASE_LOCATION, unique_folder_name, extracted_folder_name, image
        )
        if isfile(challenge_image_path):
            challenge_image_file = ContentFile(
                get_file_content(challenge_image_path, "rb"), image
            )
        else:
            challenge_image_file = None
    else:
        challenge_image_file = None
    files["challenge_image_file"] = challenge_image_file

    # Check for challenge description file
    challenge_config_location = join(
        BASE_LOCATION, unique_folder_name, extracted_folder_name
    )
    is_valid, message = is_challenge_config_yaml_html_field_valid(
        yaml_file_data, "description", challenge_config_location
    )
    if not is_valid:
        error_messages.append(message)
    else:
        yaml_file_data["description"] = get_value_from_field(
            yaml_file_data, challenge_config_location, "description"
        )

    # Check for evaluation details file
    is_valid, message = is_challenge_config_yaml_html_field_valid(
        yaml_file_data, "evaluation_details", challenge_config_location
    )
    if not is_valid:
        error_messages.append(message)
    else:
        yaml_file_data["evaluation_details"] = get_value_from_field(
            yaml_file_data, challenge_config_location, "evaluation_details"
        )

    # Check for terms and conditions file
    is_valid, message = is_challenge_config_yaml_html_field_valid(
        yaml_file_data, "terms_and_conditions", challenge_config_location
    )
    if not is_valid:
        error_messages.append(message)
    else:
        yaml_file_data["terms_and_conditions"] = get_value_from_field(
            yaml_file_data, challenge_config_location, "terms_and_conditions"
        )

    # Check for submission guidelines file
    is_valid, message = is_challenge_config_yaml_html_field_valid(
        yaml_file_data, "submission_guidelines", challenge_config_location
    )
    if not is_valid:
        error_messages.append(message)
    else:
        yaml_file_data["submission_guidelines"] = get_value_from_field(
            yaml_file_data, challenge_config_location, "submission_guidelines"
        )

    # Check for evaluation script path
    evaluation_script = yaml_file_data.get("evaluation_script")
    if evaluation_script:
        evaluation_script_path = join(
            challenge_config_location, evaluation_script
        )
        # Check for evaluation script file in extracted zip folder
        if isfile(evaluation_script_path):
            challenge_evaluation_script_file = read_file_data_as_content_file(
                evaluation_script_path, "rb", evaluation_script_path
            )
            files[
                "challenge_evaluation_script_file"
            ] = challenge_evaluation_script_file
        else:
            message = "ERROR: No evaluation script is present in the zip file. Please add it and then try again!"
            error_messages.append(message)
    else:
        message = "ERROR: There is no key for evaluation script in YAML file. Please add it and then try again!"
        error_messages.append(message)

    if not len(error_messages):
        serializer = ZipChallengeSerializer(
            data=yaml_file_data,
            context={
                "request": request,
                "challenge_host_team": challenge_host_team,
                "image": challenge_image_file,
                "evaluation_script": challenge_evaluation_script_file,
                "github_repository": request.data["GITHUB_REPOSITORY"],
            },
        )
        if not serializer.is_valid():
            message = "ERROR: Challenge metadata has following schema errors:\n {}".format(
                str(serializer.errors)
            )
            error_messages.append(message)
            return error_messages, yaml_file_data, files

    # Check for leaderboards
    leaderboard = yaml_file_data.get("leaderboard")
    leaderboard_ids = []
    if leaderboard:
        error = False
        if "schema" not in leaderboard[0]:
            message = "ERROR: There is no leaderboard schema in the YAML configuration file."
            error_messages.append(message)
            error = True
        if "default_order_by" not in leaderboard[0].get("schema"):
            message = "ERROR: There is no 'default_order_by' key in leaderboard schema."
            error_messages.append(message)
            error = True
        if "labels" not in leaderboard[0].get("schema"):
            message = "ERROR: There is no 'labels' key in leaderboard schema."
            error_messages.append(message)
            error = True

        if not error:
            for data in leaderboard:
                serializer = LeaderboardSerializer(
                    data=data, context={"config_id": data["id"]}
                )
                if not serializer.is_valid():
                    serializer_error = str(serializer.errors)
                    message = "ERROR: Leaderboard {} has following schema errors:\n {}".format(
                        data["id"], serializer_error
                    )
                    error_messages.append(message)
                else:
                    leaderboard_ids.append(data["id"])
    else:
        message = "ERROR: There is no key leaderboard in the YAML file."
        error_messages.append(message)

    # Check for challenge phases
    challenge_phases_data = yaml_file_data.get("challenge_phases")
    if not challenge_phases_data:
        message = "ERROR: No challenge phase key found. Please add challenge phases in YAML file and try again!"
        error_messages.append(message)
        return error_messages, yaml_file_data, files

    phase_ids = []
    files["challenge_test_annotation_files"] = []
    for data in challenge_phases_data:
        test_annotation_file = data.get("test_annotation_file")
        if test_annotation_file:
            test_annotation_file_path = join(
                challenge_config_location, test_annotation_file
            )
            if isfile(test_annotation_file_path):
                challenge_test_annotation_file = (
                    read_file_data_as_content_file(
                        test_annotation_file_path,
                        "rb",
                        test_annotation_file_path,
                    )
                )
                files["challenge_test_annotation_files"].append(
                    challenge_test_annotation_file
                )
            else:
                message = (
                    "ERROR: No test annotation file found in zip file"
                    "for challenge phase {}".format(data["name"])
                )
                error_messages.append(message)
        else:
            files["challenge_test_annotation_files"].append(None)

        if data.get("max_submissions_per_month", None) is None:
            data["max_submissions_per_month"] = data.get(
                "max_submissions", None
            )

        is_valid, message = is_challenge_phase_config_yaml_html_field_valid(
            data, "description", challenge_config_location
        )
        if not is_valid:
            error_messages.append(message)
        else:
            data["description"] = get_value_from_field(
                data, challenge_config_location, "description"
            )

        if data.get("is_submission_public") and data.get(
            "is_restricted_to_select_one_submission"
        ):
            message = (
                "ERROR: is_submission_public can't be 'True' for for challenge phase '{}'"
                " with is_restricted_to_select_one_submission 'True'. "
                " Please change is_submission_public to 'False'"
                " then try again!".format(data["name"])
            )
            error_messages.append(message)

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
                                message = "ERROR: Please include at least one option in attribute for challenge phase {}".format(
                                    data["id"]
                                )
                                error_messages.append(message)
                    else:
                        message = (
                            "ERROR: Please ensure that the submission meta attribute types for attribute in "
                            "challenge phase {} are from among the following: boolean, text, radio or checkbox.".format(
                                data["id"]
                            )
                        )
                        error_messages.append(message)
                else:
                    missing_keys_string = ", ".join(missing_keys)
                    message = "ERROR: Please enter the following to the submission meta attribute in challenge phase {}: {}".format(
                        data["id"], missing_keys_string
                    )
                    error_messages.append(message)
        if test_annotation_file:
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
            message = "ERROR: Challenge phase {} has following schema errors:\n {}".format(
                data["id"], serializer_error
            )
            error_messages.append(message)
        else:
            phase_ids.append(data["id"])

    # Check for dataset splits
    dataset_splits = yaml_file_data.get("dataset_splits")
    dataset_splits_ids = []
    if dataset_splits:
        for split in dataset_splits:
            name = split.get("name")
            if not name:
                message = (
                    "ERROR: There is no name for dataset split {}.".format(
                        split.get("id")
                    )
                )
                error_messages.append(message)

        for split in dataset_splits:
            serializer = DatasetSplitSerializer(
                data=split, context={"config_id": split["id"]}
            )
            if not serializer.is_valid():
                serializer_error = str(serializer.errors)
                message = "ERROR: Dataset split {} has following schema errors:\n {}".format(
                    split["id"], serializer_error
                )
                error_messages.append(message)
            else:
                dataset_splits_ids.append(split["id"])

    else:
        message = "ERROR: There is no key for dataset splits."
        error_messages.append(message)

    # Check for challenge phase splits
    challenge_phase_splits = yaml_file_data.get("challenge_phase_splits")
    if challenge_phase_splits:
        phase_split = 1
        exclude_fields = ["challenge_phase", "dataset_split", "leaderboard"]
        for data in challenge_phase_splits:
            if not is_challenge_phase_split_mapping_valid(
                phase_ids, leaderboard_ids, dataset_splits_ids, data
            ):
                message = (
                    "ERROR: Challenge phase split {} has invalid keys "
                    "for challenge_phase_id, leaderboard_id, dataset_split_id"
                ).format(phase_split)
                error_messages.append(message)

            serializer = ZipChallengePhaseSplitSerializer(
                data=data, context={"exclude_fields": exclude_fields}
            )
            if not serializer.is_valid():
                serializer_error = str(serializer.errors)
                message = "ERROR: Challenege phase split {} has following schema errors:\n {}".format(
                    phase_split, serializer_error
                )
                error_messages.append(message)
            phase_split += 1
    else:
        message = "ERROR: There is no key for challenge phase splits."
        error_messages.append(message)

    return error_messages, yaml_file_data, files
