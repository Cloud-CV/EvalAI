import logging
import os
import shutil
import tempfile
import traceback

from challenges.models import (
    Challenge,
    ChallengePhase
)
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import HttpRequest

from evalai.celery import app
from participants.models import ParticipantTeam
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge
)
from rest_framework import status
from rest_framework.response import Response
from .models import Submission
from .serializers import SubmissionSerializer
from .utils import get_file_from_url
from .sender import publish_submission_message

logger = logging.getLogger(__name__)


@app.task
def download_file_and_publish_submission_message(
    file_url,
    challenge_id,
    challenge_phase_id
):
    try:
        downloaded_file = get_file_from_url(file_url)
        print(downloaded_file, downloaded_file['temp_dir_path'], downloaded_file['name'])
        file_path = os.path.join(downloaded_file['temp_dir_path'], downloaded_file['name'])

        with open(file_path, 'r') as f:
            input_file = SimpleUploadedFile(
                downloaded_file['name'],
                f.read().encode(),
                content_type="multipart/form-data"
            )
            print(input_file, type(input_file))
        data = {'input_file': input_file, 'status': Submission.SUBMITTED}
        serializer = SubmissionSerializer(
            data=data,
            context={
                'participant_team': participant_team,
                'challenge_phase': challenge_phase,
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            submission = serializer.instance

                # publish messages in the submission worker queue
            publish_submission_message(challenge_phase.challenge.pk, challenge_phase.pk, submission.pk)
            logger.info("Message published to submission worker successfully!")
            shutil.rmtree(downloaded_file['temp_dir_path'])
    except:
        input_file = SimpleUploadedFile(
            'link_error.txt',
            request.data['input_file'].encode(),
            content_type="multipart/form-data"
        )
        data = {'input_file': input_file, 'status': Submission.FAILED}
        serializer = SubmissionSerializer(
            data=data,
            context={
                'participant_team': participant_team,
                'challenge_phase': challenge_phase,
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            submission = serializer.instance
            submission.status = Submission.FAILED
            submission.save()

