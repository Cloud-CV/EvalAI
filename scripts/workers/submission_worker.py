from __future__ import absolute_import
import contextlib
import django
import importlib
import os
import pika
import requests
import shutil
import socket
import sys
import traceback
import yaml
import zipfile

from os.path import dirname, join

from django.core.files.base import ContentFile
from django.utils import timezone

# need to add django project path in sys path
# root directory : where manage.py lives
# worker is present in root-directory/scripts/workers
# but make sure that this worker is run like `python scripts/workers/submission_worker.py`
DJANGO_PROJECT_PATH = dirname(dirname(dirname(os.path.abspath(__file__))))

COMPUTE_DIRECTORY_PATH = join(dirname(dirname(os.path.abspath(__file__))), 'compute')

# default settings module will be `dev`, to override it pass
# as command line arguments
DJANGO_SETTINGS_MODULE = 'settings.dev'
if len(sys.argv) == 2:
    DJANGO_SETTINGS_MODULE = sys.argv[1]


sys.path.insert(0, DJANGO_PROJECT_PATH)
sys.path.append(COMPUTE_DIRECTORY_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)
django.setup()

from challenges.models import Challenge     # noqa
from jobs.models import Submission          # noqa


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
        print 'Failed to fetch file from {}, error {}'.format(url, e)
        traceback.print_exc()
        response = None

    if response and response.status_code == 200:
        with open(download_location, 'w') as f:
            f.write(response.content)


def download_and_extract_zip_file(url, download_location, extract_location):
    '''
        * Function to extract download a zip file, extract it and then removes the zip file.
        * `download_location` should include name of file as well.
    '''
    try:
        response = requests.get(url)
    except Exception as e:
        print 'Failed to fetch file from {}, error {}'.format(url, e)
        response = None

    if response and response.status_code == 200:
        with open(download_location, 'w') as f:
            f.write(response.content)
        # extract zip file
        zip_ref = zipfile.ZipFile(download_location, 'r')
        zip_ref.extractall(extract_location)
        zip_ref.close()
        # delete zip file
        try:
            os.remove(download_location)
        except Exception as e:
            print 'Failed to remove zip file {}, error {}'.format(download_location, e)
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
        url = "{0}{1}".format("http://localhost:8000/media/", url)

    elif DJANGO_SETTINGS_MODULE == "settings.test":
        url = "{0}{1}".format("http://testserver/", url)

    return url


def extract_challenge_data(challenge, phases):
    '''
        * Expects a challenge object and an array of phase object
        * Extracts `evaluation_script` for challenge and `annotation_file` for each phase

    '''

    challenge_data_directory = CHALLENGE_DATA_DIR.format(challenge_id=challenge.id)
    evaluation_script_url = challenge.evaluation_script
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
        annotation_file_url = phase.test_annotation
        annotation_file_url = return_file_url_per_environment(annotation_file_url)
        annotation_file_name = os.path.basename(phase.test_annotation.name)
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge.id][phase.id] = annotation_file_name
        annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(challenge_id=challenge.id, phase_id=phase.id,
                                                                 annotation_file=annotation_file_name)
        download_and_extract_file(annotation_file_url, annotation_file_path)

    # import the challenge after everything is finished
    challenge_module = importlib.import_module(CHALLENGE_IMPORT_STRING.format(challenge_id=challenge.id))
    EVALUATION_SCRIPTS[challenge.id] = challenge_module


def load_active_challenges():
    '''
         * Fetches active challenges and corresponding active phases for it.
    '''
    q_params = {'published': True}
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
        print 'Submission {} does not exist'.format(submission_id)
        traceback.print_exc()

    submission_input_file = submission.input_file
    submission_input_file = return_file_url_per_environment(submission_input_file)

    submission_data_directory = SUBMISSION_DATA_DIR.format(submission_id=submission.id)
    submission_input_file_name = os.path.basename(submission.input_file.name)
    submission_input_file_path = SUBMISSION_INPUT_FILE_PATH.format(submission_id=submission.id,
                                                                   input_file=submission_input_file_name)
    # create submission directory
    create_dir_as_python_package(submission_data_directory)

    download_and_extract_file(submission_input_file, submission_input_file_path)


def run_submission(challenge_id, phase_id, submission_id, user_annotation_file_path):
    '''
        * receives a challenge id, phase id and user annotation file path
        * checks whether the corresponding evaluation script for the challenge exists or not
        * checks the above for annotation file
        * calls evaluation script via subprocess passing annotation file and user_annotation_file_path as argument
    '''
    annotation_file_name = PHASE_ANNOTATION_FILE_NAME_MAP.get(challenge_id).get(phase_id)
    annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(challenge_id=challenge_id, phase_id=phase_id,
                                                             annotation_file=annotation_file_name)
    submission_data_dir = SUBMISSION_DATA_DIR.format(submission_id=submission_id)
    # create a temporary run directory under submission directory, so that
    # main directory does not gets polluted
    temp_run_dir = join(submission_data_dir, 'run')
    create_dir(temp_run_dir)

    stdout_file_name = 'temp_stdout.txt'
    stderr_file_name = 'temp_stderr.txt'

    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        submission = None
    stdout_file = join(temp_run_dir, stdout_file_name)
    stderr_file = join(temp_run_dir, stderr_file_name)

    stdout = open(stdout_file, 'a+')
    stderr = open(stderr_file, 'a+')

    # call `main` from globals and set `status` to running and hence `started_at`
    submission.status = Submission.RUNNING
    submission.save()
    with stdout_redirect(stdout) as new_stdout, stderr_redirect(stderr) as new_stderr:      # noqa
        EVALUATION_SCRIPTS[challenge_id].evaluate(annotation_file_path, user_annotation_file_path)
    # after the execution is finished, set `status` to finished and hence `completed_at`
    submission.status = Submission.FINISHED
    submission.save()
    stderr.close()
    stdout.close()
    stderr_content = open(stderr_file, 'r').read()
    stdout_content = open(stdout_file, 'r').read()

    # TODO :: see if two updates can be combine into a single update.
    with open(stdout_file, 'r') as stdout:
        stdout_content = stdout.read()
        submission.stdout_file.save('stdout.txt', ContentFile(stdout_content))
    with open(stderr_file, 'r') as stderr:
        stderr_content = stderr.read()
        submission.stderr_file.save('stderr.txt', ContentFile(stderr_content))

    # delete the complete temp run directory
    shutil.rmtree(temp_run_dir)


def process_submission_message(message):
    challenge_id = message.get('challenge_id')
    phase_id = message.get('phase_id')
    submission_id = message.get('submission_id')
    extract_submission_data(submission_id)
    user_annotation_file_path = join(SUBMISSION_DATA_DIR.format(submission_id=submission_id), 'user_output.txt')
    run_submission(challenge_id, phase_id, submission_id, user_annotation_file_path)


def process_add_challenge_message(message):
    challenge_id = message.get('challenge_id')

    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        print 'Challenge {} does not exist'.format(challenge_id)
        traceback.print_exc()

    phases = challenge.challengephase_set.all()
    extract_challenge_data(challenge, phases)


def process_submission_callback(ch, method, properties, body):
    try:
        print(" [x] Received %r" % body, properties, method)
        body = yaml.safe_load(body)
        process_submission_message(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print 'Error in receiving message from submission queue with error {}'.format(e)
        traceback.print_exc()


def add_challenge_callback(ch, method, properties, body):
    try:
        print(" [x] Received %r" % body, properties, method)
        body = yaml.safe_load(body)
        process_add_challenge_message(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print 'Error in receiving message from add challenge queue with error {}'.format(e)
        traceback.print_exc()


def main():

    # before starting, make sure that everything is cleaned
    # delete `challenge_data` and `submission_files` directory completely
    try:
        shutil.rmtree(CHALLENGE_DATA_BASE_DIR)
    except OSError as e:
        print 'Failed to remove directory {} with error {}'.format(CHALLENGE_DATA_BASE_DIR, e)

    try:
        shutil.rmtree(SUBMISSION_DATA_BASE_DIR)
    except OSError as e:
        print 'Failed to remove directory {} with error {}'.format(SUBMISSION_DATA_BASE_DIR, e)

    # print tempfile.mkdtemp()
    create_dir_as_python_package(COMPUTE_DIRECTORY_PATH)

    load_active_challenges()

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))

    channel = connection.channel()
    channel.exchange_declare(exchange='evalai_submissions', type='topic')

    # name can be a combination of hostname + process id
    # host name : to easily identify that the worker is running on which instance
    # process id : to add uniqueness in case more than one worker is running on the same instance
    add_challenge_queue_name = '{hostname}_{process_id}'.format(hostname=socket.gethostname(),
                                                                process_id=str(os.getpid()))

    channel.queue_declare(queue='submission_task_queue', durable=True)

    # reason for using `exclusive` instead of `autodelete` is that
    # challenge addition queue should have only have one consumer on the connection
    # that creates it.
    channel.queue_declare(queue=add_challenge_queue_name, durable=True, exclusive=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')

    # create submission base data directory
    create_dir_as_python_package(SUBMISSION_DATA_BASE_DIR)

    channel.queue_bind(exchange='evalai_submissions', queue='submission_task_queue', routing_key='submission.*.*')
    channel.basic_consume(process_submission_callback, queue='submission_task_queue')

    channel.queue_bind(exchange='evalai_submissions', queue=add_challenge_queue_name, routing_key='challenge.add.*')
    channel.basic_consume(add_challenge_callback, queue=add_challenge_queue_name)

    channel.start_consuming()


if __name__ == '__main__':
    main()
