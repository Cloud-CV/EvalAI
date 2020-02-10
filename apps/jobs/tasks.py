import logging
import os
import shutil

from challenges.models import ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from evalai.celery import app
from participants.models import ParticipantTeam
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge
)
from .models import Submission
from .serializers import SubmissionSerializer
from .utils import get_file_from_url
from .sender import publish_submission_message

logger = logging.getLogger(__name__)


@app.task
def download_file_and_publish_submission_message(
    request_data,
    user_pk,
    request_method,
    challenge_phase_id
):
    """
    Download submission file from url and send it for the evaluation
    """
    user = User.objects.get(pk=user_pk)
    challenge_phase = ChallengePhase.objects.get(
        pk=challenge_phase_id
    )
    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        user, challenge_phase.challenge.pk
    )
    participant_team = ParticipantTeam.objects.get(
        pk=participant_team_id
    )
    request = HttpRequest()
    request.method = request_method
    request.user = user
    try:
        downloaded_file = get_file_from_url(request_data["file_url"])
        file_path = os.path.join(downloaded_file["temp_dir_path"], downloaded_file["name"])

        with open(file_path, 'rb') as f:
            input_file = SimpleUploadedFile(
                downloaded_file["name"],
                f.read(),
                content_type="multipart/form-data"
            )
        data = {
            "input_file": input_file,
            "method_name": request_data["method_name"],
            "method_description": request_data["method_description"],
            "project_url": request_data["project_url"],
            "publication_url": request_data["publication_url"],
            "status": Submission.SUBMITTED
        }
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
            publish_submission_message({
                "challenge_pk": challenge_phase.challenge.pk,
                "phase_pk": challenge_phase.pk,
                "submission_pk": submission.pk
            })
            logger.info("Message published to submission worker successfully!")
            shutil.rmtree(downloaded_file['temp_dir_path'])
    except Exception as e:
        logger.exception(
            "Exception while downloading and sending submission for evaluation {}"
            .format(e)
        )
