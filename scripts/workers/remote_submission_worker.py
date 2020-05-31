from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import importlib
import json
import logging
import os
import requests
import signal
import shutil
import sys
import tempfile
import time
import traceback
import zipfile

from os.path import join

# all challenge and submission will be stored in temp directory
BASE_TEMP_DIR = tempfile.mkdtemp()
COMPUTE_DIRECTORY_PATH = join(BASE_TEMP_DIR, "compute")

logger = logging.getLogger(__name__)

AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
DJANGO_SERVER = os.environ.get("DJANGO_SERVER", "localhost")
DJANGO_SERVER_PORT = os.environ.get("DJANGO_SERVER_PORT", "8000")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")

CHALLENGE_DATA_BASE_DIR = join(COMPUTE_DIRECTORY_PATH, "challenge_data")
SUBMISSION_DATA_BASE_DIR = join(COMPUTE_DIRECTORY_PATH, "submission_files")
CHALLENGE_DATA_DIR = join(CHALLENGE_DATA_BASE_DIR, "challenge_{challenge_id}")
PHASE_DATA_BASE_DIR = join(CHALLENGE_DATA_DIR, "phase_data")
PHASE_DATA_DIR = join(PHASE_DATA_BASE_DIR, "phase_{phase_id}")
PHASE_ANNOTATION_FILE_PATH = join(PHASE_DATA_DIR, "{annotation_file}")
SUBMISSION_DATA_DIR = join(
    SUBMISSION_DATA_BASE_DIR, "submission_{submission_id}"
)
SUBMISSION_INPUT_FILE_PATH = join(SUBMISSION_DATA_DIR, "{input_file}")
CHALLENGE_IMPORT_STRING = "challenge_data.challenge_{challenge_id}"
EVALUATION_SCRIPTS = {}
URLS = {
    "get_message_from_sqs_queue": "/api/jobs/challenge/queues/{}/",
    "delete_message_from_sqs_queue": "/api/jobs/queues/{}/",
    "get_submission_by_pk": "/api/jobs/submission/{}",
    "get_challenge_phases_by_challenge_pk": "/api/challenges/{}/phases/",
    "get_challenge_by_queue_name": "/api/challenges/challenge/queues/{}/",
    "get_challenge_phase_by_pk": "/api/challenges/challenge/{}/challenge_phase/{}",
    "update_submission_data": "/api/jobs/challenge/{}/update_submission/",
}
EVALAI_ERROR_CODES = [400, 401, 406]

# map of challenge id : phase id : phase annotation file name
# Use: On arrival of submission message, lookup here to fetch phase file name
# this saves db query just to fetch phase annotation file name
PHASE_ANNOTATION_FILE_NAME_MAP = {}


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


class ExecutionTimeLimitExceeded(Exception):
    pass


@contextlib.contextmanager
def stdout_redirect(where):
    sys.stdout = where
    try:
        yield where
    finally:
        sys.stdout = sys.__stdout__


@contextlib.contextmanager
def stderr_redirect(where):
    sys.stderr = where
    try:
        yield where
    finally:
        sys.stderr = sys.__stderr__


def alarm_handler(signum, frame):
    raise ExecutionTimeLimitExceeded


def download_and_extract_file(url, download_location):
    """
        * Function to extract download a file.
        * `download_location` should include name of file as well.
    """
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        traceback.print_exc()
        response = None

    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            f.write(response.content)


def download_and_extract_zip_file(url, download_location, extract_location):
    """
        * Function to extract download a zip file, extract it and then removes the zip file.
        * `download_location` should include name of file as well.
    """
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        response = None

    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            f.write(response.content)
        # extract zip file
        zip_ref = zipfile.ZipFile(download_location, "r")
        zip_ref.extractall(extract_location)
        zip_ref.close()
        # delete zip file
        try:
            os.remove(download_location)
        except Exception as e:
            logger.error(
                "Failed to remove zip file {}, error {}".format(
                    download_location, e
                )
            )
            traceback.print_exc()


def create_dir(directory):
    """
        Creates a directory if it does not exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_dir_as_python_package(directory):
    """
        Create a directory and then makes it a python
        package by creating `__init__.py` file.
    """
    create_dir(directory)
    init_file_path = join(directory, "__init__.py")
    with open(init_file_path, "w") as init_file:  # noqa
        # to create empty file
        pass


def return_url_per_environment(url):
    base_url = "http://{0}:{1}".format(DJANGO_SERVER, DJANGO_SERVER_PORT)
    url = "{0}{1}".format(base_url, url)
    return url


def load_challenge():
    """
        Creates python package for a challenge and extracts relevant data
    """
    # make sure that the challenge base directory exists
    create_dir_as_python_package(CHALLENGE_DATA_BASE_DIR)
    try:
        challenge = get_challenge_by_queue_name()
    except Exception:
        logger.exception(
            "Challenge with queue name %s does not exists" % (QUEUE_NAME)
        )
        raise
    challenge_pk = challenge.get("id")
    phases = get_challenge_phases_by_challenge_pk(challenge_pk)
    extract_challenge_data(challenge, phases)


def extract_challenge_data(challenge, phases):
    """
        * Expects a challenge object and an array of phase object
        * Extracts `evaluation_script` for challenge and `annotation_file` for each phase
    """
    challenge_data_directory = CHALLENGE_DATA_DIR.format(
        challenge_id=challenge.get("id")
    )
    evaluation_script_url = challenge.get("evaluation_script")
    create_dir_as_python_package(challenge_data_directory)

    # set entry in map
    PHASE_ANNOTATION_FILE_NAME_MAP[challenge.get("id")] = {}

    challenge_zip_file = join(
        challenge_data_directory,
        "challenge_{}.zip".format(challenge.get("id")),
    )
    download_and_extract_zip_file(
        evaluation_script_url, challenge_zip_file, challenge_data_directory
    )

    phase_data_base_directory = PHASE_DATA_BASE_DIR.format(
        challenge_id=challenge.get("id")
    )
    create_dir(phase_data_base_directory)

    for phase in phases:
        phase_data_directory = PHASE_DATA_DIR.format(
            challenge_id=challenge.get("id"), phase_id=phase.get("id")
        )
        # create phase directory
        create_dir(phase_data_directory)
        annotation_file_url = phase.get("test_annotation")
        annotation_file_name = os.path.basename(phase.get("test_annotation"))
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge.get("id")][
            phase.get("id")
        ] = annotation_file_name
        annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(
            challenge_id=challenge.get("id"),
            phase_id=phase.get("id"),
            annotation_file=annotation_file_name,
        )
        download_and_extract_file(annotation_file_url, annotation_file_path)
    try:
        # import the challenge after everything is finished
        challenge_module = importlib.import_module(
            CHALLENGE_IMPORT_STRING.format(challenge_id=challenge.get("id"))
        )
        EVALUATION_SCRIPTS[challenge.get("id")] = challenge_module
    except Exception:
        logger.exception(
            "Exception raised while creating Python module for challenge_id: %s"
            % (challenge.get("id"))
        )
        raise


def process_submission_callback(body):
    try:
        logger.info("[x] Received submission message %s" % body)
        process_submission_message(body)
    except Exception as e:
        logger.exception(
            "Exception while processing message from submission queue with error {}".format(
                e
            )
        )


def process_submission_message(message):
    """
    Extracts the submission related metadata from the message
    and send the submission object for evaluation
    """
    challenge_pk = int(message.get("challenge_pk"))
    phase_pk = message.get("phase_pk")
    submission_pk = message.get("submission_pk")
    submission_instance = extract_submission_data(submission_pk)

    # so that the further execution does not happen
    if not submission_instance:
        return
    challenge = get_challenge_by_queue_name()
    remote_evaluation = challenge.get("remote_evaluation")
    challenge_phase = get_challenge_phase_by_pk(challenge_pk, phase_pk)
    if not challenge_phase:
        logger.exception(
            "Challenge Phase {} does not exist for queue {}".format(
                phase_pk, QUEUE_NAME
            )
        )
        raise
    user_annotation_file_path = join(
        SUBMISSION_DATA_DIR.format(submission_id=submission_pk),
        os.path.basename(submission_instance.get("input_file")),
    )
    run_submission(
        challenge_pk,
        challenge_phase,
        submission_instance,
        user_annotation_file_path,
        remote_evaluation,
    )


def extract_submission_data(submission_pk):
    """
        * Expects submission id and extracts input file for it.
    """

    submission = get_submission_by_pk(submission_pk)
    if not submission:
        logger.critical("Submission {} does not exist".format(submission_pk))
        traceback.print_exc()
        # return from here so that the message can be acked
        # This also indicates that we don't want to take action
        # for message corresponding to which submission entry
        # does not exist
        return

    submission_input_file = submission.get("input_file")

    submission_data_directory = SUBMISSION_DATA_DIR.format(
        submission_id=submission.get("id")
    )
    submission_input_file_name = os.path.basename(submission_input_file)
    submission_input_file_path = SUBMISSION_INPUT_FILE_PATH.format(
        submission_id=submission.get("id"),
        input_file=submission_input_file_name,
    )
    create_dir_as_python_package(submission_data_directory)
    download_and_extract_file(
        submission_input_file, submission_input_file_path
    )
    return submission


def get_request_headers():
    headers = {"Authorization": "Token {}".format(AUTH_TOKEN)}
    return headers


def make_request(url, method, data=None):
    headers = get_request_headers()
    if method == "GET":
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        return response.json()

    elif method == "PUT":
        try:
            response = requests.put(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.exception(
                "The worker is not able to establish connection with EvalAI due to {}"
                % (response.json())
            )
            raise
        except requests.exceptions.HTTPError:
            logger.exception(f"The request to URL {url} is failed due to {response.json()}")
            raise
        return response.json()

    elif method == "PATCH":
        try:
            response = requests.patch(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        except requests.exceptions.HTTPError:
            logger.info(f"The request to URL {url} is failed due to {response.json()}")
            raise
        return response.json()

    elif method == "POST":
        try:
            response = requests.post(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        except requests.exceptions.HTTPError:
            logger.info(f"The request to URL {url} is failed due to {response.json()}")
            raise
        return response.json()


def get_message_from_sqs_queue():
    url = URLS.get("get_message_from_sqs_queue").format(QUEUE_NAME)
    url = return_url_per_environment(url)
    response = make_request(url, "GET")
    return response


def delete_message_from_sqs_queue(receipt_handle):
    url = URLS.get("delete_message_from_sqs_queue").format(
        QUEUE_NAME
    )
    url = return_url_per_environment(url)
    response = make_request(url, "POST", data={
        "receipt_handle": receipt_handle
    })  # noqa
    return response


def get_submission_by_pk(submission_pk):
    url = URLS.get("get_submission_by_pk").format(submission_pk)
    url = return_url_per_environment(url)
    response = make_request(url, "GET")
    return response


def get_challenge_phases_by_challenge_pk(challenge_pk):
    url = URLS.get("get_challenge_phases_by_challenge_pk").format(challenge_pk)
    url = return_url_per_environment(url)
    response = make_request(url, "GET")
    return response


def get_challenge_by_queue_name():
    url = URLS.get("get_challenge_by_queue_name").format(QUEUE_NAME)
    url = return_url_per_environment(url)
    response = make_request(url, "GET")
    return response


def get_challenge_phase_by_pk(challenge_pk, challenge_phase_pk):
    url = URLS.get("get_challenge_phase_by_pk").format(
        challenge_pk, challenge_phase_pk
    )
    url = return_url_per_environment(url)
    response = make_request(url, "GET")
    return response


def update_submission_data(data, challenge_pk, submission_pk):
    url = URLS.get("update_submission_data").format(challenge_pk)
    url = return_url_per_environment(url)
    response = make_request(url, "PUT", data=data)
    return response


def update_submission_status(data, challenge_pk):
    url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
    url = return_url_per_environment(url)
    response = make_request(url, "PATCH", data=data)
    return response


def read_file_content(file_path):
    with open(file_path, "r") as obj:
        file_content = obj.read()
        if not file_content:
            file_content = " "
        return file_content


def run_submission(
    challenge_pk,
    challenge_phase,
    submission,
    user_annotation_file_path,
    remote_evaluation,
):
    """
    * Checks whether the corresponding evaluation script and the annotation file for the challenge exists or not
    * Calls evaluation script to evaluate the particular submission

    Arguments:
        challenge_pk  -- challenge Id in which the submission is created
        challenge_phase  -- challenge phase JSON object in which the submission is created
        submission  -- JSON object for the submisson
        user_annotation_file_path  -- File submitted by user as a submission
    """
    # Send the submission data to the evaluation script
    # so that challenge hosts can use data for webhooks or any other service.

    submission_output = None
    phase_pk = challenge_phase.get("id")
    submission_pk = submission.get("id")
    annotation_file_name = PHASE_ANNOTATION_FILE_NAME_MAP[challenge_pk][
        phase_pk
    ]
    annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(
        challenge_id=challenge_pk,
        phase_id=phase_pk,
        annotation_file=annotation_file_name,
    )
    submission_data_dir = SUBMISSION_DATA_DIR.format(
        submission_id=submission.get("id")
    )

    submission_data = {
        "submission_status": "running",
        "submission": submission_pk,
    }
    update_submission_status(submission_data, challenge_pk)
    status = "running"
    # create a temporary run directory under submission directory, so that
    # main directory does not gets polluted
    temp_run_dir = join(submission_data_dir, "run")
    create_dir(temp_run_dir)

    stdout_file = join(temp_run_dir, "temp_stdout.txt")
    stderr_file = join(temp_run_dir, "temp_stderr.txt")

    stdout = open(stdout_file, "a+")
    stderr = open(stderr_file, "a+")

    try:
        logger.info(
            "Sending submission {} for evaluation".format(submission_pk)
        )
        with stdout_redirect(stdout), stderr_redirect(stderr):
            submission_output = EVALUATION_SCRIPTS[challenge_pk].evaluate(
                annotation_file_path,
                user_annotation_file_path,
                challenge_phase.get("codename"),
                submission_metadata=submission,
            )
        if remote_evaluation:
            return
    except Exception:
        status = "failed"
        stderr.write(traceback.format_exc())
        stdout.close()
        stderr.close()

        stdout_content = read_file_content(stdout_file)
        stderr_content = read_file_content(stderr_file)

        submission_data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "submission_status": status,
            "stdout": stdout_content,
            "stderr": stderr_content,
        }
        update_submission_data(submission_data, challenge_pk, submission_pk)

        shutil.rmtree(temp_run_dir)
        return

    stdout.close()
    stderr.close()

    stdout_content = read_file_content(stdout_file)
    stderr_content = read_file_content(stderr_file)

    submission_data = {
        "challenge_phase": phase_pk,
        "submission": submission_pk,
        "submission_status": status,
        "stdout": stdout_content,
        "stderr": stderr_content,
    }

    if "result" in submission_output:
        status = "finished"
        submission_data["result"] = json.dumps(submission_output.get("result"))
        submission_data["metadata"] = json.dumps(
            submission_output.get("submission_metadata")
        )
        submission_data["submission_status"] = status
    else:
        status = "failed"
        submission_data["submission_status"] = status
    update_submission_data(submission_data, challenge_pk, submission_pk)
    shutil.rmtree(temp_run_dir)
    return


def main():
    killer = GracefulKiller()
    logger.info(
        "Using {0} as temp directory to store data".format(BASE_TEMP_DIR)
    )
    create_dir_as_python_package(COMPUTE_DIRECTORY_PATH)
    sys.path.append(COMPUTE_DIRECTORY_PATH)

    # create submission base data directory
    create_dir_as_python_package(SUBMISSION_DATA_BASE_DIR)
    load_challenge()

    while True:
        logger.info(
            "Fetching new messages from the queue {}".format(QUEUE_NAME)
        )
        message = get_message_from_sqs_queue()
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            submission = get_submission_by_pk(submission_pk)
            if submission:
                if submission.get("status") == "finished":
                    message_receipt_handle = message.get("receipt_handle")
                    delete_message_from_sqs_queue(message_receipt_handle)
                elif submission.get("status") == "running":
                    continue
                else:
                    message_receipt_handle = message.get("receipt_handle")
                    logger.info(
                        "Processing message body: {}".format(message_body)
                    )
                    process_submission_callback(message_body)
                    # Let the queue know that the message is processed
                    delete_message_from_sqs_queue(message_receipt_handle)
        time.sleep(5)
        if killer.kill_now:
            break


if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
