from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import django
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

from django.utils import timezone

# all challenge and submission will be stored in temp directory
BASE_TEMP_DIR = tempfile.mkdtemp()
COMPUTE_DIRECTORY_PATH = join(BASE_TEMP_DIR, 'compute')

logger = logging.getLogger(__name__)
django.setup()

DJANGO_SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'settings.dev')
DJANGO_SERVER = os.environ.get('DJANGO_SERVER', "localhost")

CHALLENGE_DATA_BASE_DIR = join(COMPUTE_DIRECTORY_PATH, 'challenge_data')
SUBMISSION_DATA_BASE_DIR = join(COMPUTE_DIRECTORY_PATH, 'submission_files')
CHALLENGE_DATA_DIR = join(CHALLENGE_DATA_BASE_DIR, 'challenge_{challenge_id}')
PHASE_DATA_BASE_DIR = join(CHALLENGE_DATA_DIR, 'phase_data')
PHASE_DATA_DIR = join(PHASE_DATA_BASE_DIR, 'phase_{phase_id}')
PHASE_ANNOTATION_FILE_PATH = join(PHASE_DATA_DIR, '{annotation_file}')
SUBMISSION_DATA_DIR = join(SUBMISSION_DATA_BASE_DIR, 'submission_{submission_id}')
SUBMISSION_INPUT_FILE_PATH = join(SUBMISSION_DATA_DIR, '{input_file}')
CHALLENGE_IMPORT_STRING = 'challenge_data.challenge_{challenge_id}'
EVALUATION_SCRIPTS = {}

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
    '''
        * Function to extract download a file.
        * `download_location` should include name of file as well.
    '''
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error('Failed to fetch file from {}, error {}'.format(url, e))
        traceback.print_exc()
        response = None

    if response and response.status_code == 200:
        with open(download_location, 'wb') as f:
            f.write(response.content)


def download_and_extract_zip_file(url, download_location, extract_location):
    '''
        * Function to extract download a zip file, extract it and then removes the zip file.
        * `download_location` should include name of file as well.
    '''
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error('Failed to fetch file from {}, error {}'.format(url, e))
        response = None

    if response and response.status_code == 200:
        with open(download_location, 'wb') as f:
            f.write(response.content)
        # extract zip file
        zip_ref = zipfile.ZipFile(download_location, 'r')
        zip_ref.extractall(extract_location)
        zip_ref.close()
        # delete zip file
        try:
            os.remove(download_location)
        except Exception as e:
            logger.error('Failed to remove zip file {}, error {}'.format(download_location, e))
            traceback.print_exc()


def create_dir(directory):
    '''
        Creates a directory if it does not exists
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_dir_as_python_package(directory):
    '''
        Create a directory and then makes it a python
        package by creating `__init__.py` file.
    '''
    create_dir(directory)
    init_file_path = join(directory, '__init__.py')
    with open(init_file_path, 'w') as init_file:        # noqa
        # to create empty file
        pass


def return_url_per_environment(url):

    base_url = "http://{0}:8000".format(DJANGO_SERVER)
    url = "{0}{1}".format(base_url, url)

    if DJANGO_SETTINGS_MODULE == "settings.test":
        url = "{0}{1}".format("http://testserver", url)

    return url


def load_challenge(challenge_pk, queue_name, auth_token):
    '''
        Creates python package for a challenge and extracts relevant data
    '''
    # make sure that the challenge base directory exists
    create_dir_as_python_package(CHALLENGE_DATA_BASE_DIR)
    challenge = get_challenge_by_pk(challenge_pk, queue_name, auth_token)
    phases = get_challenge_phases_by_challenge_pk(challenge_pk, queue_name, auth_token)
    extract_challenge_data(challenge, phases)


def extract_challenge_data(challenge, phases):
    '''
        * Expects a challenge object and an array of phase object
        * Extracts `evaluation_script` for challenge and `annotation_file` for each phase

    '''
    challenge_data_directory = CHALLENGE_DATA_DIR.format(challenge_id=challenge.get('id'))
    evaluation_script_url = challenge.get('evaluation_script')
    # evaluation_script_url = return_url_per_environment(evaluation_script_url)
    # create challenge directory as package
    create_dir_as_python_package(challenge_data_directory)

    # set entry in map
    PHASE_ANNOTATION_FILE_NAME_MAP[str(challenge.get('id'))] = {}

    challenge_zip_file = join(challenge_data_directory, 'challenge_{}.zip'.format(challenge.get('id')))
    download_and_extract_zip_file(evaluation_script_url, challenge_zip_file, challenge_data_directory)

    phase_data_base_directory = PHASE_DATA_BASE_DIR.format(challenge_id=challenge.get('id'))
    create_dir(phase_data_base_directory)

    for phase in phases:
        phase_data_directory = PHASE_DATA_DIR.format(challenge_id=challenge.get('id'), phase_id=phase.get('id'))
        # create phase directory
        create_dir(phase_data_directory)
        annotation_file_url = phase.get('test_annotation')
        # annotation_file_url = return_url_per_environment(annotation_file_url)
        annotation_file_name = os.path.basename(phase.get('test_annotation'))
        PHASE_ANNOTATION_FILE_NAME_MAP[str(challenge.get('id'))][str(phase.get('id'))] = annotation_file_name
        annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(challenge_id=challenge.get('id'),
                                                                 phase_id=phase.get('id'),
                                                                 annotation_file=annotation_file_name)
        download_and_extract_file(annotation_file_url, annotation_file_path)
    try:
        # import the challenge after everything is finished
        challenge_module = importlib.import_module(CHALLENGE_IMPORT_STRING.format(challenge_id=challenge.get('id')))
        EVALUATION_SCRIPTS[str(challenge.get('id'))] = challenge_module
    except:
        logger.exception('Exception raised while creating Python module for challenge_id: %s' % (challenge.get('id')))
        raise


def process_submission_callback(body, queue_name, auth_token):
    try:
        logger.info("[x] Received submission message %s" % body)
        process_submission_message(body, queue_name, auth_token)
    except Exception as e:
        logger.exception('Exception while receiving message from submission queue with error {}'.format(e))


def process_submission_message(message, queue_name, auth_token):
    '''
    Extracts the submission related metadata from the message
    and send the submission object for evaluation
    '''
    challenge_pk = message.get('challenge_pk')
    phase_pk = message.get('phase_pk')
    submission_pk = message.get('submission_pk')
    submission_instance = extract_submission_data(submission_pk, queue_name, auth_token)

    # so that the further execution does not happen
    if not submission_instance:
        return

    challenge_phase = get_challenge_phase_by_pk(phase_pk, queue_name, auth_token)
    if not challenge_phase:
        logger.exception('Challenge Phase {} does not exist for queue {}'.format(phase_pk, queue_name))
        raise
    user_annotation_file_path = join(SUBMISSION_DATA_DIR.format(submission_id=submission_pk),
                                     os.path.basename(submission_instance.get('input_file')))
    run_submission(challenge_pk,
                   challenge_phase,
                   submission_instance,
                   user_annotation_file_path,
                   queue_name,
                   auth_token)


def extract_submission_data(submission_pk, queue_name, auth_token):
    '''
        * Expects submission id and extracts input file for it.
    '''

    submission = get_submission_by_pk(submission_pk, queue_name, auth_token)
    if not submission:
        logger.critical('Submission {} does not exist'.format(submission_pk))
        traceback.print_exc()
        # return from here so that the message can be acked
        # This also indicates that we don't want to take action
        # for message corresponding to which submission entry
        # does not exist
        return None

    submission_input_file = submission.get('input_file')

    submission_data_directory = SUBMISSION_DATA_DIR.format(submission_id=submission.get('id'))
    submission_input_file_name = os.path.basename(submission_input_file)
    submission_input_file_path = SUBMISSION_INPUT_FILE_PATH.format(submission_id=submission.get('id'),
                                                                   input_file=submission_input_file_name)
    # create submission directory
    create_dir_as_python_package(submission_data_directory)

    download_and_extract_file(submission_input_file, submission_input_file_path)

    return submission


def get_request_headers(auth_token):
    headers = {'Authorization': 'Token {}'.format(auth_token)}
    return headers


def get_message_from_sqs_queue(challenge_pk, queue_name, auth_token):
    url = '/api/jobs/challenge/{}/queue/{}/'.format(challenge_pk, queue_name)
    url = return_url_per_environment(url)
    headers = get_request_headers(auth_token)
    message = requests.get(url, headers=headers)
    if message.status_code == 200:
        message = message.json()
        return message
    return None


def delete_message_from_sqs_queue(receipt_handle, queue_name, auth_token):
    url = '/api/jobs/challenge/queue/{}/receipt/{}/'.format(queue_name, receipt_handle)
    url = return_url_per_environment(url)
    headers = get_request_headers(auth_token)
    message = requests.get(url, headers=headers)
    if message.status_code == 200:
        return None
    logger.exception("A message with receipt handle {} is not deleted successfully"
                     " for challenge queue {}".format(receipt_handle, queue_name))
    return None


def get_submission_by_pk(submission_pk, queue_name, auth_token):
    url = '/api/jobs/submission/{}/queue/{}/'.format(submission_pk, queue_name)
    url = return_url_per_environment(url)
    headers = get_request_headers(auth_token)
    submission = requests.get(url, headers=headers)
    if submission.status_code == 200:
        submission = submission.json()
        return submission
    return None


def get_challenge_phases_by_challenge_pk(challenge_pk, queue_name, auth_token):
    url = '/api/challenges/challenge/{}/phases/queue/{}/'.format(challenge_pk, queue_name)
    url = return_url_per_environment(url)
    headers = get_request_headers(auth_token)
    challenge_phases = requests.get(url, headers=headers)
    if challenge_phases.status_code == 200:
        challenge_phases = challenge_phases.json()
        return challenge_phases
    return None


def get_challenge_by_pk(challenge_pk, queue_name, auth_token):
    url = '/api/challenges/challenge/{}/queue/{}/'.format(challenge_pk, queue_name)
    url = return_url_per_environment(url)
    headers = get_request_headers(auth_token)
    challenge = requests.get(url, headers=headers)
    if challenge.status_code == 200:
        challenge = challenge.json()
        return challenge
    return None


def get_challenge_phase_by_pk(challenge_phase_pk, queue_name, auth_token):
    url = '/api/challenges/phase/{}/queue/{}/'.format(challenge_phase_pk, queue_name)
    url = return_url_per_environment(url)
    headers = get_request_headers(auth_token)
    challenge_phase = requests.get(url, headers=headers)
    if challenge_phase.status_code == 200:
        challenge_phase = challenge_phase.json()
        return challenge_phase
    return None


def update_submission_data(data, challenge_pk, queue_name, auth_token):
    url = '/api/jobs/v1/challenge/{}/update_submission/queue/{}/'.format(challenge_pk, queue_name)
    url = return_url_per_environment(url)
    request_payload = data
    headers = get_request_headers(auth_token)
    submission = requests.put(url=url, data=request_payload, headers=headers)
    if submission.status_code == 200:
        submission = submission.json()
        return submission
    return None


def update_submission_status(challenge_pk, submission_pk, data, queue_name, auth_token):
    url = '/api/jobs/challenge/{}/submission/{}/queue/{}/'.format(challenge_pk, submission_pk, queue_name)
    url = return_url_per_environment(url)
    request_payload = data
    headers = get_request_headers(auth_token)
    submission = requests.put(url=url, data=request_payload, headers=headers)
    if submission.status_code == 200:
        submission = submission.json()
        return submission
    return None


def read_file_content(file_path):
    with open(file_path, 'r') as obj:
        file_content = obj.read()
        return file_content


def run_submission(challenge_pk, challenge_phase, submission, user_annotation_file_path, queue_name, auth_token):
    """
    * It checks whether the corresponding evaluation script and the annotation file for the challenge exists or not
    * It calls evaluation script via subprocess passing annotation file and user_annotation_file_path as argument

    Arguments:
        challenge_pk  -- challenge ID in which the submission is created
        challenge_phase  -- challenge phase ID in which the submission is created
        submission  -- JSON object for the submisson
        user_annotation_file_path  -- File submitted by user as a submission
        queue_name  -- The secret token that challenge host possess
        auth_token  -- The authentication token of the challenge host
    """
    # Send the submission data to the evaluation script
    # so that challenge hosts can use data for webhooks or any other service.

    submission_output = None
    phase_pk = challenge_phase.get('id')
    submission_pk = submission.get('id')
    annotation_file_name = PHASE_ANNOTATION_FILE_NAME_MAP[str(challenge_pk)][str(phase_pk)]
    annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(challenge_id=challenge_pk, phase_id=phase_pk,
                                                             annotation_file=annotation_file_name)
    submission_data_dir = SUBMISSION_DATA_DIR.format(submission_id=submission.get('id'))

    submission_data = {
        'status': 'running',
        'started_at': timezone.now()
    }
    update_submission_status(challenge_pk, submission_pk, submission_data, queue_name, auth_token)

    # create a temporary run directory under submission directory, so that
    # main directory does not gets polluted
    temp_run_dir = join(submission_data_dir, 'run')
    create_dir(temp_run_dir)

    stdout_file = join(temp_run_dir, 'temp_stdout.txt')
    stderr_file = join(temp_run_dir, 'temp_stderr.txt')

    stdout = open(stdout_file, 'a+')
    stderr = open(stderr_file, 'a+')

    try:
        logger.info("Sending submission {} for evaluation".format(submission_pk))
        with stdout_redirect(stdout) as new_stdout, stderr_redirect(stderr) as new_stderr: # noqa
            submission_output = EVALUATION_SCRIPTS[challenge_pk].evaluate(
                annotation_file_path,
                user_annotation_file_path,
                challenge_phase.get('codename'),
                submission_metadata=submission)
    except:
        stderr.write(traceback.format_exc())
        stdout.close()
        stderr.close()

        stdout_content = read_file_content(stdout_file)
        stderr_content = read_file_content(stderr_file)

        submission_data = {
            'challenge_phase': phase_pk,
            'submission': submission_pk,
            'submission_status': 'failed',
            'stdout': stdout_content,
            'stderr': stderr_content,
        }
        update_submission_data(submission_data, challenge_pk, queue_name, auth_token)

        shutil.rmtree(temp_run_dir)
        return

    if 'result' in submission_output:
        stdout.close()
        stderr.close()

        stdout_content = read_file_content(stdout_file)
        stderr_content = read_file_content(stderr_file)

        submission_data = {
            'challenge_phase': phase_pk,
            'submission': submission_pk,
            'submission_status': 'finished',
            'stdout': stdout_content,
            'stderr': stderr_content,
            'result': json.dumps(submission_output.get('result')),
            'metadata': json.dumps(submission_output.get('submission_metadata')),
        }
        update_submission_data(submission_data, challenge_pk, queue_name, auth_token)
    else:
        stderr.write(traceback.format_exc())
        stdout.close()
        stderr.close()

        stdout_content = read_file_content(stdout_file)
        stderr_content = read_file_content(stderr_file)

        submission_data = {
            'challenge_phase': phase_pk,
            'submission': submission_pk,
            'submission_status': 'failed',
            'stdout': stdout_content,
            'stderr': stderr_content,
        }
        update_submission_data(submission_data, challenge_pk, queue_name, auth_token)

    shutil.rmtree(temp_run_dir)
    return


def main():
    killer = GracefulKiller()
    logger.info('Using {0} as temp directory to store data'.format(BASE_TEMP_DIR))
    create_dir_as_python_package(COMPUTE_DIRECTORY_PATH)
    sys.path.append(COMPUTE_DIRECTORY_PATH)

    auth_token = os.environ.get('AUTH_TOKEN')
    challenge_pk = os.environ.get('CHALLENGE_PK')
    queue_name = os.environ.get('CHALLENGE_QUEUE', 'evalai_submission_queue')

    # create submission base data directory
    create_dir_as_python_package(SUBMISSION_DATA_BASE_DIR)

    load_challenge(challenge_pk, queue_name, auth_token)

    while True:
        logger.info("Fetching new messages from the queue...")
        message = get_message_from_sqs_queue(challenge_pk, queue_name, auth_token)
        message_body = message['message_body']
        if message_body is not None:
            submission_pk = message_body.get('submission_pk')
            submission = get_submission_by_pk(submission_pk, queue_name, auth_token)
            if submission is not None:
                if submission['status'] == 'finished':
                    message_receipt_handle = message['message_receipt_handle']
                    delete_message_from_sqs_queue(message_receipt_handle, queue_name, auth_token)
                elif submission['status'] == 'running':
                    continue
                else:
                    message_receipt_handle = message['message_receipt_handle']
                    logger.info('Processing message body: {}'.format(message['message_body']))
                    process_submission_callback(message['message_body'], queue_name, auth_token)
                    # Let the queue know that the message is processed
                    delete_message_from_sqs_queue(message_receipt_handle, queue_name, auth_token)
        time.sleep(5)
        if killer.kill_now:
            break


if __name__ == '__main__':
    main()
    logger.info("Quitting Submission Worker.")
