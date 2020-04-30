import requests
import zipfile
import yaml

from os.path import basename, isfile, join
from rest_framework import status


def write_file(output_path, mode, file_content):
    with open(output_path, mode) as file:
        file.write(file_content)


def extract_zip_file(file_path, mode, output_path):
    zip_ref = zipfile.ZipFile(file_path, mode)
    zip_ref.extractall(output_path)
    zip_ref.close()
    return zip_ref


def get_yaml_files_from_challenge_config(zip_ref):
    yaml_file_count = 0
    yaml_file_name = None
    extracted_folder_name = None
    for name in zip_ref.namelist():
        if (name.endswith(".yaml") or name.endswith(".yml")) and (
                not name.startswith("__MACOSX")
        ):
            yaml_file_name = name
            extracted_folder_name = yaml_file_name.split(basename(yaml_file_name))[0]
            yaml_file_count += 1

    if not yaml_file_count:
        return yaml_file_count, None, None
    return yaml_file_count, yaml_file_name, extracted_folder_name


def read_yaml_file(file_path, mode):
    with open(file_path, mode) as stream:
        yaml_file_data = yaml.safe_load(stream)
    return yaml_file_data


def get_yaml_read_error_description(exc):
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


def is_valid_challenge_config_yaml_field(yaml_file_data, key, base_location):
    value = yaml_file_data.get(key)
    message = ""
    is_valid = False
    is_error = False
    if value:
        file_path = join(base_location, value)
        if file_path.endswith(".html") and isfile(file_path):
            is_valid = True
        else:
            message = "WARNING: No {}.html file is present in the zip file.".format(key)
    else:
        message = "ERROR: There is no key for {} in YAML file".format(key)
        is_error = True
    return is_valid, message, is_error


def is_valid_challenge_phase_config_yaml_field(yaml_file_data, key, base_location):
    value = yaml_file_data.get(key)
    message = ""
    is_valid = False
    if value:
        file_path = join(base_location, value)
        if file_path.endswith(".html") and isfile(file_path):
            is_valid = True
        else:
            message = (" WARNING: There is no file for phase "
                       " {} in phase {}.".format(key, yaml_file_data["name"]))
    else:
        message = " ERROR: There is no key for phase {} in phase {}.".format(key, yaml_file_data["name"])
    return is_valid, message


def download_and_write_file(url, stream, output_path, mode):
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
                "Unable to process the uploaded zip file. "
                "Please try again!"
            )
    except requests.exceptions.RequestException:
        message = (
            "A server error occured while processing zip file. "
            "Please try again!"
        )
    return is_success, message


def validate_challenge_phase_split(phase_ids, leaderboard_ids, dataset_split_ids, phase_split):
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

