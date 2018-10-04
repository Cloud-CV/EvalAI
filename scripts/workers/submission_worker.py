
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import boto3
import botocore
import contextlib
import django
import importlib
import logging
import os
import requests
import signal
import shutil
import sys
import tempfile
import time
import traceback
import yaml
import zipfile

from os.path import join

from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings

# all challenge and submission will be stored in temp directory
BASE_TEMP_DIR = tempfile.mkdtemp()
COMPUTE_DIRECTORY_PATH = join(BASE_TEMP_DIR, 'compute')

logger = logging.getLogger(__name__)
django.setup()

DJANGO_SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'settings.dev')
DJANGO_SERVER = os.environ.get('DJANGO_SERVER', "localhost")

from challenges.models import (Challenge,
                               ChallengePhase,
                               ChallengePhaseSplit,
                               LeaderboardData) # noqa

from jobs.models import Submission          # noqa
from jobs.serializers import SubmissionSerializer # noqa


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

django.db.close_old_connections()


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


def return_file_url_per_environment(url):

    if DJANGO_SETTINGS_MODULE == "settings.dev":
        base_url = "http://{0}:8000".format(DJANGO_SERVER)
        url = "{0}{1}".format(base_url, url)

    elif DJANGO_SETTINGS_MODULE == "settings.test":
        url = "{0}{1}".format("http://testserver", url)

    return url


def extract_challenge_data(challenge, phases):
    '''
        * Expects a challenge object and an array of phase object
        * Extracts `evaluation_script` for challenge and `annotation_file` for each phase

    '''

    challenge_data_directory = CHALLENGE_DATA_DIR.format(challenge_id=challenge.id)
    evaluation_script_url = challenge.evaluation_script.url
    evaluation_script_url = return_file_url_per_environment(evaluation_script_url)
    # create challenge directory as package
    create_dir_as_python_package(challenge_data_directory)

    # set entry in map
    PHASE_ANNOTATION_FILE_NAME_MAP[challenge.id] = {}

    challenge_zip_file = join(challenge_data_directory, 'challenge_{}.zip'.format(challenge.id))
    download_and_extract_zip_file(evaluation_script_url, challenge_zip_file, challenge_data_directory)

    phase_data_base_directory = PHASE_DATA_BASE_DIR.format(challenge_id=challenge.id)
    create_dir(phase_data_base_directory)

    for phase in phases:
        phase_data_directory = PHASE_DATA_DIR.format(challenge_id=challenge.id, phase_id=phase.id)
        # create phase directory
        create_dir(phase_data_directory)
        annotation_file_url = phase.test_annotation.url
        annotation_file_url = return_file_url_per_environment(annotation_file_url)
        annotation_file_name = os.path.basename(phase.test_annotation.name)
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge.id][phase.id] = annotation_file_name
        annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(challenge_id=challenge.id, phase_id=phase.id,
                                                                 annotation_file=annotation_file_name)
        download_and_extract_file(annotation_file_url, annotation_file_path)

    try:
        # TODO: Add a better approach instead of adding to sys.path
        sys.path.append(os.path.join(COMPUTE_DIRECTORY_PATH, 'challenge_data', 'challenge_{}'.format(challenge.id)))
        # import the challenge after everything is finished
        challenge_module = importlib.import_module(CHALLENGE_IMPORT_STRING.format(challenge_id=challenge.id))
        EVALUATION_SCRIPTS[challenge.id] = challenge_module
    except:
        logger.error('Error while creating Python module for challenge_id: %s' % (challenge.id))
        traceback.print_exc()


def load_active_challenges():
    '''
         * Fetches active challenges and corresponding active phases for it.
    '''
    q_params = {'approved_by_admin': True}
    q_params['start_date__lt'] = timezone.now()
    q_params['end_date__gt'] = timezone.now()

    # make sure that the challenge base directory exists
    create_dir_as_python_package(CHALLENGE_DATA_BASE_DIR)

    active_challenges = Challenge.objects.filter(**q_params)

    for challenge in active_challenges:
        phases = challenge.challengephase_set.all()
        extract_challenge_data(challenge, phases)


def extract_submission_data(submission_id):
    '''
        * Expects submission id and extracts input file for it.
    '''

    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        logger.critical('Submission {} does not exist'.format(submission_id))
        traceback.print_exc()
        # return from here so that the message can be acked
        # This also indicates that we don't want to take action
        # for message corresponding to which submission entry
        # does not exist
        return None

    submission_input_file = submission.input_file.url
    submission_input_file = return_file_url_per_environment(submission_input_file)

    submission_data_directory = SUBMISSION_DATA_DIR.format(submission_id=submission.id)
    submission_input_file_name = os.path.basename(submission.input_file.name)
    submission_input_file_path = SUBMISSION_INPUT_FILE_PATH.format(submission_id=submission.id,
                                                                   input_file=submission_input_file_name)
    # create submission directory
    create_dir_as_python_package(submission_data_directory)

    download_and_extract_file(submission_input_file, submission_input_file_path)

    return submission


def run_submission(challenge_id, challenge_phase, submission, user_annotation_file_path):
    '''
        * receives a challenge id, phase id and user annotation file path
        * checks whether the corresponding evaluation script for the challenge exists or not
        * checks the above for annotation file
        * calls evaluation script via subprocess passing annotation file and user_annotation_file_path as argument
    '''

    # Use the submission serializer to send relevant data to evaluation script
    # so that challenge hosts can use data for webhooks or any other service.
    submission_serializer = SubmissionSerializer(submission)

    submission_output = None
    phase_id = challenge_phase.id
    annotation_file_name = PHASE_ANNOTATION_FILE_NAME_MAP.get(challenge_id).get(phase_id)
    annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(challenge_id=challenge_id, phase_id=phase_id,
                                                             annotation_file=annotation_file_name)
    submission_data_dir = SUBMISSION_DATA_DIR.format(submission_id=submission.id)
    # create a temporary run directory under submission directory, so that
    # main directory does not gets polluted
    temp_run_dir = join(submission_data_dir, 'run')
    create_dir(temp_run_dir)

    stdout_file_name = 'temp_stdout.txt'
    stderr_file_name = 'temp_stderr.txt'

    stdout_file = join(temp_run_dir, stdout_file_name)
    stderr_file = join(temp_run_dir, stderr_file_name)

    stdout = open(stdout_file, 'a+')
    stderr = open(stderr_file, 'a+')

    # call `main` from globals and set `status` to running and hence `started_at`
    submission.status = Submission.RUNNING
    submission.started_at = timezone.now()
    submission.save()
    try:
        successful_submission_flag = True
        with stdout_redirect(stdout) as new_stdout, stderr_redirect(stderr) as new_stderr:      # noqa
            submission_output = EVALUATION_SCRIPTS[challenge_id].evaluate(
                annotation_file_path,
                user_annotation_file_path,
                challenge_phase.codename,
                submission_metadata=submission_serializer.data,
            )
        '''
        A submission will be marked successful only if it is of the format
            {
               "result":[
                  {
                     "split_codename_1":{
                        "key1":30,
                        "key2":50,
                     }
                  },
                  {
                     "split_codename_2":{
                        "key1":90,
                        "key2":10,
                     }
                  },
                  {
                     "split_codename_3":{
                        "key1":100,
                        "key2":45,
                     }
                  }
               ],
               "submission_metadata": {'foo': 'bar'},
               "submission_result": ['foo', 'bar'],
            }
        '''
        if 'result' in submission_output:

            leaderboard_data_list = []
            for split_result in submission_output['result']:
                # get split_code_name that is the key of the result
                split_code_name = list(split_result.keys())[0]

                # Check if the challenge_phase_split exists for the challenge_phaseand dataset_split
                try:
                    challenge_phase_split = ChallengePhaseSplit.objects.get(challenge_phase=challenge_phase,
                                                                            dataset_split__codename=split_code_name)
                except:
                    stderr.write("ORGINIAL EXCEPTION: No such relation between Challenge Phase and DatasetSplit"
                                 " specified by Challenge Host \n")
                    stderr.write(traceback.format_exc())
                    successful_submission_flag = False
                    break

                # Check if the dataset_split exists for the codename in the result
                try:
                    dataset_split = challenge_phase_split.dataset_split
                except:
                    stderr.write("ORGINIAL EXCEPTION: The codename specified by your Challenge Host doesn't match"
                                 " with that in the evaluation Script.\n")
                    stderr.write(traceback.format_exc())
                    successful_submission_flag = False
                    break

                leaderboard_data = LeaderboardData()
                leaderboard_data.challenge_phase_split = challenge_phase_split
                leaderboard_data.submission = submission
                leaderboard_data.leaderboard = challenge_phase_split.leaderboard
                leaderboard_data.result = split_result.get(dataset_split.codename)

                leaderboard_data_list.append(leaderboard_data)

            if successful_submission_flag:
                LeaderboardData.objects.bulk_create(leaderboard_data_list)

        # Once the submission_output is processed, then save the submission object with appropriate status
        else:
            successful_submission_flag = False

    except:
        stderr.write(traceback.format_exc())
        successful_submission_flag = False

    submission_status = Submission.FINISHED if successful_submission_flag else Submission.FAILED
    submission.status = submission_status
    submission.completed_at = timezone.now()
    submission.save()

    # after the execution is finished, set `status` to finished and hence `completed_at`
    if submission_output:
        output = {}
        output['result'] = submission_output.get('result', '')
        submission.output = output

        # Save submission_result_file
        submission_result = submission_output.get('submission_result', '')
        submission.submission_result_file.save('submission_result.json', ContentFile(submission_result))

        # Save submission_metadata_file
        submission_metadata = submission_output.get('submission_metadata', '')
        submission.submission_metadata_file.save('submission_metadata.json', ContentFile(submission_metadata))

    submission.save()

    stderr.close()
    stdout.close()
    stderr_content = open(stderr_file, 'r').read()
    stdout_content = open(stdout_file, 'r').read()

    # TODO :: see if two updates can be combine into a single update.
    with open(stdout_file, 'r') as stdout:
        stdout_content = stdout.read()
        submission.stdout_file.save('stdout.txt', ContentFile(stdout_content))
    if (submission_status is Submission.FAILED):
        with open(stderr_file, 'r') as stderr:
            stderr_content = stderr.read()
            submission.stderr_file.save('stderr.txt', ContentFile(stderr_content))

    # delete the complete temp run directory
    shutil.rmtree(temp_run_dir)


def process_submission_message(message):
    '''
    Extracts the submission related metadata from the message
    and send the submission object for evaluation
    '''
    challenge_id = message.get('challenge_id')
    phase_id = message.get('phase_id')
    submission_id = message.get('submission_id')
    submission_instance = extract_submission_data(submission_id)

    # so that the further execution does not happen
    if not submission_instance:
        return

    try:
        challenge_phase = ChallengePhase.objects.get(id=phase_id)
    except ChallengePhase.DoesNotExist:
        logger.critical('Challenge Phase {} does not exist'.format(phase_id))
        traceback.print_exc()
        return

    user_annotation_file_path = join(SUBMISSION_DATA_DIR.format(submission_id=submission_id),
                                     os.path.basename(submission_instance.input_file.name))
    run_submission(challenge_id, challenge_phase, submission_instance, user_annotation_file_path,)


def process_add_challenge_message(message):
    challenge_id = message.get('challenge_id')

    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        logger.critical('Challenge {} does not exist'.format(challenge_id))
        traceback.print_exc()

    phases = challenge.challengephase_set.all()
    extract_challenge_data(challenge, phases)


def process_submission_callback(body):
    try:
        logger.info("[x] Received submission message %s" % body)
        body = yaml.safe_load(body)
        body = dict((k, int(v)) for k, v in body.items())
        process_submission_message(body)
    except Exception as e:
        logger.error('Error in receiving message from submission queue with error {}'.format(e))
        traceback.print_exc()


def get_or_create_sqs_queue():
    """
    Returns:
        Returns the SQS Queue object
    """
    sqs = boto3.resource('sqs',
                         endpoint_url=os.environ.get('AWS_SQS_ENDPOINT', 'http://sqs:9324'),
                         region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                         aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                         aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),)

    AWS_SQS_QUEUE_NAME = os.environ.get('AWS_SQS_QUEUE_NAME', 'evalai_submission_queue')
    # Check if the FIFO queue exists. If no, then create one
    try:
        queue = sqs.get_queue_by_name(QueueName=AWS_SQS_QUEUE_NAME)
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            if settings.DEBUG:
                queue = sqs.create_queue(QueueName=AWS_SQS_QUEUE_NAME)
            else:
                # create a FIFO queue in the production environment
                name = AWS_SQS_QUEUE_NAME + '.fifo'
                queue = sqs.create_queue(
                    QueueName=name,
                    Attributes={
                        'FifoQueue': 'true',
                        'ContentBasedDeduplication': 'true'
                    }
                )
        else:
            logger.error('Cannot get or create queue!')
    return queue


def main():
    killer = GracefulKiller()
    logger.info('Using {0} as temp directory to store data'.format(BASE_TEMP_DIR))
    create_dir_as_python_package(COMPUTE_DIRECTORY_PATH)
    sys.path.append(COMPUTE_DIRECTORY_PATH)

    load_active_challenges()

    # create submission base data directory
    create_dir_as_python_package(SUBMISSION_DATA_BASE_DIR)
    queue = get_or_create_sqs_queue()

    while True:
        for message in queue.receive_messages():
            # Print out the body of the message
            logger.info('Processing message body: {0}'.format(message.body))
            process_submission_callback(message.body)
            # Let the queue know that the message is processed
            message.delete()
        if killer.kill_now:
            break
        time.sleep(0.1)


if __name__ == '__main__':
    main()
    logger.info("Quitting Submission Worker.")
