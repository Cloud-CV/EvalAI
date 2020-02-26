import contextlib
import logging
import os
import requests
import signal
import traceback
from os.path import join
import zipfile

AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")

logger = logging.getLogger(__name__)

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

class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


class ExecutionTimeLimitExceeded(Exception):
    pass


class EvalAI_Interface:
    def __init__(self, AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME):
        self.AUTH_TOKEN = AUTH_TOKEN
        self.EVALAI_API_SERVER = EVALAI_API_SERVER
        self.QUEUE_NAME = QUEUE_NAME
        self.URLS = {
            "get_message_from_sqs_queue": "/api/jobs/challenge/queues/{}/",
            "delete_message_from_sqs_queue": "/api/jobs/queues/{}/",
            "get_submission_by_pk": "/api/jobs/submission/{}",
            "get_challenge_phases_by_challenge_pk": "/api/challenges/{}/phases/",
            "get_challenge_by_queue_name": "/api/challenges/challenge/queues/{}/",
            "get_challenge_phase_by_pk": "/api/challenges/challenge/{}/challenge_phase/{}",
            "update_submission_data": "/api/jobs/challenge/{}/update_submission/",
                }

    def get_request_headers(self):
        headers = {"Authorization": "Token {}".format(self.AUTH_TOKEN)}
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
                logger.exception(
                    "The request to URL {} is failed due to {}"
                    % (url, response.json())
                )
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
                logger.info(
                    "The request to URL {} is failed due to {}"
                    % (url, response.json())
                )
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
                logger.info(
                    "The request to URL {} is failed due to {}"
                    % (url, response.json())
                )
                raise
            return response.json()

    def return_url_per_environment(self, url):
        base_url = "{0}".format(self.EVALAI_API_SERVER)
        url = "{0}{1}".format(base_url, url)
        return url

    def get_message_from_sqs_queue(self):
        url = self.URLS.get("get_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def delete_message_from_sqs_queue(self, receipt_handle):
        url = self.URLS.get("delete_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        data = {"receipt_handle": receipt_handle}
        response = self.make_request(url, "POST", data)  # noqa
        return response

    def get_submission_by_pk(self, submission_pk):
        url = self.URLS.get("get_submission_by_pk").format(submission_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_phases_by_challenge_pk(self, challenge_pk):
        url = self.URLS.get("get_challenge_phases_by_challenge_pk").format(
            challenge_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_by_queue_name(self):
        url = self.URLS.get("get_challenge_by_queue_name").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_phase_by_pk(self, challenge_pk, challenge_phase_pk):
        url = self.URLS.get("get_challenge_phase_by_pk").format(
            challenge_pk, challenge_phase_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def update_submission_data(self, data, challenge_pk, submission_pk):
        url = self.URLS.get("update_submission_data").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_submission_status(self, data, challenge_pk):
        url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PATCH", data=data)
        return response

def download_and_extract_file(url, download_location):
    """
        * Function to extract download a file.
        * `download_location` should include name of file as well.
    """
    try:
        response = requests.get(url, stream=True)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        traceback.print_exc()
        response = None

    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

def extract_zip_file(download_location, extract_location):
    """
    Helper function to extract zip file
    Params:
        * `download_location`: Location of zip file
        * `extract_location`: Location of directory for extracted file
    """
    zip_ref = zipfile.ZipFile(download_location, "r")
    zip_ref.extractall(extract_location)
    zip_ref.close()


def delete_zip_file(download_location):
    """
    Helper function to remove zip file from location `download_location`
    Params:
        * `download_location`: Location of file to be removed.
    """
    try:
        os.remove(download_location)
    except Exception as e:
        logger.error(
            "Failed to remove zip file {}, error {}".format(
                download_location, e
            )
        )
        traceback.print_exc()


def download_and_extract_zip_file(url, download_location, extract_location):
    """
        * Function to extract download a zip file, extract it and then removes the zip file.
        * `download_location` should include name of file as well.
    """
    try:
        response = requests.get(url, stream=True)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        response = None

    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        # extract zip file
        extract_zip_file(download_location, extract_location)
        # delete zip file
        delete_zip_file(download_location)

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
