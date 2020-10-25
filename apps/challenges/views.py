import csv
import json
import logging
import os
import random
import requests
import shutil
import tempfile
import time
import uuid
import yaml
import zipfile

from os.path import basename, isfile, join

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from yaml.scanner import ScannerError

from allauth.account.models import EmailAddress
from accounts.permissions import HasVerifiedEmail
from accounts.serializers import UserDetailsSerializer
from base.utils import (
    get_queue_name,
    get_slug,
    get_url_from_hostname,
    paginated_queryset,
    send_email,
    send_slack_notification,
)
from challenges.utils import (
    generate_presigned_url,
    get_challenge_model,
    get_challenge_phase_model,
    get_challenge_phase_split_model,
    get_dataset_split_model,
    get_leaderboard_model,
    get_participant_model,
    get_unique_alpha_numeric_key,
    is_user_in_allowed_email_domains,
    is_user_in_blocked_email_domains,
)
from challenges.challenge_config_utils import (
    download_and_write_file,
    extract_zip_file,
    validate_challenge_config_util,
)
from hosts.models import ChallengeHost, ChallengeHostTeam
from hosts.utils import (
    get_challenge_host_teams_for_user,
    is_user_a_host_of_challenge,
    get_challenge_host_team_model,
)
from jobs.filters import SubmissionFilter
from jobs.models import Submission
from jobs.serializers import (
    SubmissionSerializer,
    ChallengeSubmissionManagementSerializer,
)
from participants.models import Participant, ParticipantTeam
from participants.serializers import ParticipantTeamDetailSerializer
from participants.utils import (
    get_participant_teams_for_user,
    has_user_participated_in_challenge,
    get_participant_team_id_of_user_for_a_challenge,
    get_participant_team_of_user_for_a_challenge,
)

from .models import (
    Challenge,
    ChallengeEvaluationCluster,
    ChallengePhase,
    ChallengePhaseSplit,
    ChallengeTemplate,
    ChallengeConfiguration,
    StarChallenge,
    UserInvitation,
)
from .permissions import IsChallengeCreator
from .serializers import (
    ChallengeConfigSerializer,
    ChallengeEvaluationClusterSerializer,
    ChallengePhaseSerializer,
    ChallengePhaseCreateSerializer,
    ChallengePhaseSplitSerializer,
    ChallengeTemplateSerializer,
    ChallengeSerializer,
    DatasetSplitSerializer,
    LeaderboardSerializer,
    StarChallengeSerializer,
    UserInvitationSerializer,
    ZipChallengeSerializer,
    ZipChallengePhaseSplitSerializer,
)

from .aws_utils import (
    start_workers,
    stop_workers,
    restart_workers,
    get_logs_from_cloudwatch,
)
from .utils import (
    get_aws_credentials_for_submission,
    get_file_content,
    get_missing_keys_from_dict,
    get_challenge_template_data,
    send_emails
)

logger = logging.getLogger(__name__)

try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_list(request, challenge_host_team_pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(
            pk=challenge_host_team_pk
        )
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        challenge = Challenge.objects.filter(
            creator=challenge_host_team, is_disabled=False
        ).order_by("-id")
        paginator, result_page = paginated_queryset(challenge, request)
        serializer = ChallengeSerializer(
            result_page, many=True, context={"request": request}
        )
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == "POST":
        if not ChallengeHost.objects.filter(
            user=request.user, team_name_id=challenge_host_team_pk
        ).exists():
            response_data = {
                "error": "Sorry, you do not belong to this Host Team!"
            }
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

        serializer = ZipChallengeSerializer(
            data=request.data,
            context={
                "challenge_host_team": challenge_host_team,
                "request": request,
            },
        )
        if serializer.is_valid():
            serializer.save()
            challenge = get_challenge_model(serializer.instance.pk)
            serializer = ChallengeSerializer(challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_detail(request, challenge_host_team_pk, challenge_pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(
            pk=challenge_host_team_pk
        )
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        serializer = ChallengeSerializer(
            challenge, context={"request": request}
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:
        if request.method == "PATCH":
            serializer = ZipChallengeSerializer(
                challenge,
                data=request.data,
                context={
                    "challenge_host_team": challenge_host_team,
                    "request": request,
                },
                partial=True,
            )
        else:
            serializer = ZipChallengeSerializer(
                challenge,
                data=request.data,
                context={
                    "challenge_host_team": challenge_host_team,
                    "request": request,
                },
            )
        if serializer.is_valid():
            serializer.save()
            challenge = get_challenge_model(serializer.instance.pk)
            serializer = ChallengeSerializer(challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    elif request.method == "DELETE":
        challenge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_detail_for_challenge(request, challenge_pk):
    """
        Returns the participated team detail in the challenge
        Arguments:
            challenge_pk {int} -- Challenge primary key
        Returns:
            {dict} -- Participant team detail that has participated in the challenge
    """
    if has_user_participated_in_challenge(user=request.user, challenge_id=challenge_pk):
        participant_team_pk = get_participant_team_id_of_user_for_a_challenge(request.user, challenge_pk)
        participant_team = get_participant_model(participant_team_pk)
        serializer = ParticipantTeamDetailSerializer(participant_team)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        message = ("You are not a participant!")
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def add_participant_team_to_challenge(
    request, challenge_pk, participant_team_pk
):

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if not challenge.is_registration_open:
        response_data = {"error": "Registration is closed for this challenge!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if (
        challenge.end_date < timezone.now()
        or challenge.start_date > timezone.now()
    ):
        response_data = {
            "error": "Sorry, cannot accept participant team since challenge is not active."
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "ParticipantTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check if user is banned
    if len(challenge.banned_email_ids) > 0:
        for participant_email in participant_team.get_all_participants_email():
            if participant_email in challenge.banned_email_ids:
                message = "You're a part of {} team and it has been banned from this challenge. \
                Please contact the challenge host.".format(
                    participant_team.team_name
                )
                response_data = {"error": message}
                return Response(
                    response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                )

    # Check if user is in allowed list.
    user_email = request.user.email
    if len(challenge.allowed_email_domains) > 0:
        if not is_user_in_allowed_email_domains(user_email, challenge_pk):
            message = "Sorry, users with {} email domain(s) are only allowed to participate in this challenge."
            domains = ""
            for domain in challenge.allowed_email_domains:
                domains = "{}{}{}".format(domains, "/", domain)
            domains = domains[1:]
            response_data = {"error": message.format(domains)}
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

    # Check if user is in blocked list.
    if is_user_in_blocked_email_domains(user_email, challenge_pk):
        message = "Sorry, users with {} email domain(s) are not allowed to participate in this challenge."
        domains = ""
        for domain in challenge.blocked_email_domains:
            domains = "{}{}{}".format(domains, "/", domain)
        domains = domains[1:]
        response_data = {"error": message.format(domains)}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # check to disallow the user if he is a Challenge Host for this challenge
    participant_team_user_ids = set(
        Participant.objects.select_related("user")
        .filter(team__id=participant_team_pk)
        .values_list("user", flat=True)
    )

    for user in participant_team_user_ids:
        if has_user_participated_in_challenge(user, challenge_pk):
            response_data = {
                "error": "Sorry, other team member(s) have already participated in the Challenge."
                " Please participate with a different team!",
                "challenge_id": int(challenge_pk),
                "participant_team_id": int(participant_team_pk),
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

    if participant_team.challenge_set.filter(id=challenge_pk).exists():
        response_data = {
            "error": "Team already exists",
            "challenge_id": int(challenge_pk),
            "participant_team_id": int(participant_team_pk),
        }
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        challenge.participant_teams.add(participant_team)
        return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((ExpiringTokenAuthentication,))
def disable_challenge(request, challenge_pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge.is_disabled = True
    challenge.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def get_all_challenges(request, challenge_time):
    """
    Returns the list of all challenges
    """
    # make sure that a valid url is requested.
    if challenge_time.lower() not in ("all", "future", "past", "present"):
        response_data = {"error": "Wrong url pattern!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    q_params = {"published": True, "approved_by_admin": True}
    if challenge_time.lower() == "past":
        q_params["end_date__lt"] = timezone.now()

    elif challenge_time.lower() == "present":
        q_params["start_date__lt"] = timezone.now()
        q_params["end_date__gt"] = timezone.now()

    elif challenge_time.lower() == "future":
        q_params["start_date__gt"] = timezone.now()
    # for `all` we dont need any condition in `q_params`

    # don't return disabled challenges
    q_params["is_disabled"] = False

    challenge = Challenge.objects.filter(**q_params).order_by("-pk")
    paginator, result_page = paginated_queryset(challenge, request)
    serializer = ChallengeSerializer(
        result_page, many=True, context={"request": request}
    )
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def get_featured_challenges(request):
    """
    Returns the list of featured challenges
    """
    challenge = Challenge.objects.filter(
        featured=True,
        published=True,
        approved_by_admin=True,
        is_disabled=False,
    ).order_by("-id")
    paginator, result_page = paginated_queryset(challenge, request)
    serializer = ChallengeSerializer(
        result_page, many=True, context={"request": request}
    )
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def get_challenge_by_pk(request, pk):
    """
    Returns a particular challenge by id
    """
    try:
        if is_user_a_host_of_challenge(request.user, pk):
            challenge = Challenge.objects.get(pk=pk)
        else:
            challenge = Challenge.objects.get(
                pk=pk, approved_by_admin=True, published=True
            )
        if challenge.is_disabled:
            response_data = {"error": "Sorry, the challenge was removed!"}
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )
        serializer = ChallengeSerializer(
            challenge, context={"request": request}
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_all_participated_challenges(request, challenge_time):
    """
    Returns the list of all participated challenges
    """
    # make sure that a valid url is requested.
    if challenge_time.lower() not in ("all", "past", "present"):
        response_data = {"error": "Wrong url pattern!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    q_params = {"published": True, "approved_by_admin": True}

    if challenge_time.lower() == "past":
        q_params["end_date__lt"] = timezone.now()

    elif challenge_time.lower() == "present":
        q_params["start_date__lt"] = timezone.now()
        q_params["end_date__gt"] = timezone.now()

    # don't return disabled challenges
    q_params["is_disabled"] = False
    participant_team_ids = get_participant_teams_for_user(request.user)
    q_params["participant_teams__pk__in"] = participant_team_ids
    challenges = Challenge.objects.filter(**q_params).order_by("-pk")
    paginator, result_page = paginated_queryset(challenges, request)
    serializer = ChallengeSerializer(
        result_page, many=True, context={"request": request}
    )
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenges_based_on_teams(request):
    q_params = {"approved_by_admin": True, "published": True}
    participant_team_id = request.query_params.get("participant_team", None)
    challenge_host_team_id = request.query_params.get("host_team", None)
    mode = request.query_params.get("mode", None)

    if not participant_team_id and not challenge_host_team_id and not mode:
        response_data = {"error": "Invalid url pattern!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # either mode should be there or one of paricipant team and host team
    if mode and (participant_team_id or challenge_host_team_id):
        response_data = {"error": "Invalid url pattern!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if participant_team_id:
        q_params["participant_teams__pk"] = participant_team_id
    if challenge_host_team_id:
        q_params["creator__id"] = challenge_host_team_id

    if mode == "participant":
        participant_team_ids = get_participant_teams_for_user(request.user)
        q_params["participant_teams__pk__in"] = participant_team_ids

    elif mode == "host":
        host_team_ids = get_challenge_host_teams_for_user(request.user)
        q_params["creator__id__in"] = host_team_ids

    challenge = Challenge.objects.filter(**q_params).order_by("id")
    paginator, result_page = paginated_queryset(challenge, request)
    serializer = ChallengeSerializer(
        result_page, many=True, context={"request": request}
    )
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (
        permissions.IsAuthenticatedOrReadOnly,
        HasVerifiedEmail,
        IsChallengeCreator,
    )
)
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_phase_list(request, challenge_pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        if is_user_a_host_of_challenge(request.user, challenge_pk):
            challenge_phase = ChallengePhase.objects.filter(
                challenge=challenge
            ).order_by("pk")
        else:
            challenge_phase = ChallengePhase.objects.filter(
                challenge=challenge, is_public=True
            ).order_by("pk")
        paginator, result_page = paginated_queryset(challenge_phase, request)
        serializer = ChallengePhaseSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == "POST":
        serializer = ChallengePhaseCreateSerializer(
            data=request.data, context={"challenge": challenge}
        )
        if serializer.is_valid():
            serializer.save()
            challenge_phase = get_challenge_phase_model(serializer.instance.pk)
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (
        permissions.IsAuthenticatedOrReadOnly,
        HasVerifiedEmail,
        IsChallengeCreator,
    )
)
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_phase_detail(request, challenge_pk, pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        challenge_phase = ChallengePhase.objects.get(
            challenge=challenge, pk=pk
        )
    except ChallengePhase.DoesNotExist:
        response_data = {
            "error": "Challenge phase {} does not exist for challenge {}".format(
                pk, challenge.pk
            )
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        if not is_user_a_host_of_challenge(request.user, challenge.id):
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            serializer = ChallengePhaseCreateSerializer(
                challenge_phase, context={"request": request}
            )
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:
        if request.method == "PATCH":
            serializer = ChallengePhaseCreateSerializer(
                challenge_phase,
                data=request.data.copy(),
                context={"challenge": challenge},
                partial=True,
            )
        else:
            serializer = ChallengePhaseCreateSerializer(
                challenge_phase,
                data=request.data.copy(),
                context={"challenge": challenge},
            )
        if serializer.is_valid():
            serializer.save()
            challenge_phase = get_challenge_phase_model(serializer.instance.pk)
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    elif request.method == "DELETE":
        challenge_phase.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def challenge_phase_split_list(request, challenge_pk):
    """
    Returns the list of Challenge Phase Splits for a particular challenge
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge_phase_split = ChallengePhaseSplit.objects.filter(
        challenge_phase__challenge=challenge
    )

    # Check if user is a challenge host or participant
    challenge_host = is_user_a_host_of_challenge(request.user, challenge_pk)

    if not challenge_host:
        challenge_phase_split = challenge_phase_split.filter(
            visibility=ChallengePhaseSplit.PUBLIC
        )

    serializer = ChallengePhaseSplitSerializer(
        challenge_phase_split, many=True
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_challenge_using_zip_file(request, challenge_host_team_pk):
    """
    Creates a challenge using a zip file.
    """
    challenge_host_team = get_challenge_host_team_model(challenge_host_team_pk)

    if request.data.get("is_challenge_template"):
        is_challenge_template = True
    else:
        is_challenge_template = False

    # All files download and extract location.
    BASE_LOCATION = tempfile.mkdtemp()

    if is_challenge_template:
        template_id = int(request.data.get("template_id"))
        try:
            challenge_template = ChallengeTemplate.objects.get(
                id=template_id, is_active=True
            )
        except ChallengeTemplate.DoesNotExist:
            response_data = {
                "error": "Sorry, a server error occured while creating the challenge. Please try again!"
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        if settings.DEBUG or settings.TEST:
            template_zip_s3_url = settings.EVALAI_API_SERVER + challenge_template.template_file.url
        else:
            template_zip_s3_url = challenge_template.template_file.url

        unique_folder_name = get_unique_alpha_numeric_key(10)
        challenge_template_download_location = join(
            BASE_LOCATION, "{}.zip".format(unique_folder_name)
        )

        try:
            response = requests.get(template_zip_s3_url, stream=True)
        except Exception as e:
            logger.error(
                "Failed to fetch file from {}, error {}".format(
                    template_zip_s3_url, e
                )
            )
            response_data = {
                "error": "Sorry, there was an error in the server"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if response and response.status_code == status.HTTP_200_OK:
            with open(challenge_template_download_location, "wb") as f:
                f.write(response.content)

        try:
            zip_file = open(challenge_template_download_location, "rb")
        except Exception:
            message = (
                "A server error occured while processing zip file. "
                "Please try again!"
            )
            response_data = {"error": message}
            logger.exception(message)
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        challenge_zip_file = SimpleUploadedFile(
            zip_file.name, zip_file.read(), content_type="application/zip"
        )

        # Copy request data so that we can mutate it to add template
        challenge_data_from_hosts = request.data.copy()
        challenge_data_from_hosts["zip_configuration"] = challenge_zip_file
        serializer = ChallengeConfigSerializer(
            data=challenge_data_from_hosts, context={"request": request}
        )
    else:
        data = request.data.copy()
        serializer = ChallengeConfigSerializer(
            data=data, context={"request": request}
        )

    if serializer.is_valid():
        uploaded_zip_file = serializer.save()
        uploaded_zip_file_path = serializer.data["zip_configuration"]
    else:
        response_data = serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        response = requests.get(uploaded_zip_file_path, stream=True)
        unique_folder_name = get_unique_alpha_numeric_key(10)
        CHALLENGE_ZIP_DOWNLOAD_LOCATION = join(
            BASE_LOCATION, "{}.zip".format(unique_folder_name)
        )
        try:
            if response and response.status_code == 200:
                with open(CHALLENGE_ZIP_DOWNLOAD_LOCATION, "wb") as zip_file:
                    zip_file.write(response.content)
        except IOError:
            message = (
                "Unable to process the uploaded zip file. " "Please try again!"
            )
            response_data = {"error": message}
            logger.exception(message)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    except requests.exceptions.RequestException:
        message = (
            "A server error occured while processing zip file. "
            "Please try again!"
        )
        response_data = {"error": message}
        logger.exception(message)
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Extract zip file
    try:
        zip_ref = zipfile.ZipFile(CHALLENGE_ZIP_DOWNLOAD_LOCATION, "r")
        zip_ref.extractall(join(BASE_LOCATION, unique_folder_name))
        zip_ref.close()
    except zipfile.BadZipfile:
        message = (
            "The zip file contents cannot be extracted. "
            "Please check the format!"
        )
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Search for yaml file
    yaml_file_count = 0
    for name in zip_ref.namelist():
        if (name.endswith(".yaml") or name.endswith(".yml")) and (
            not name.startswith("__MACOSX")
        ):  # Ignore YAML File in __MACOSX Directory
            yaml_file = name
            extracted_folder_name = yaml_file.split(basename(yaml_file))[0]
            yaml_file_count += 1

    if not yaml_file_count:
        message = "There is no YAML file in zip file you uploaded!"
        response_data = {"error": message}
        logger.info(message)
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if yaml_file_count > 1:
        message = "There are {0} YAML files instead of one in zip folder!".format(
            yaml_file_count
        )
        response_data = {"error": message}
        logger.info(message)
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        with open(
            join(BASE_LOCATION, unique_folder_name, yaml_file), "r"
        ) as stream:
            yaml_file_data = yaml.safe_load(stream)
    except (yaml.YAMLError, ScannerError) as exc:
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
        message = "{} in line {}, column {}".format(
            error_description, line_number, column_number
        )
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for evaluation script path in yaml file.
    try:
        evaluation_script = yaml_file_data["evaluation_script"]
        evaluation_script_path = join(
            BASE_LOCATION,
            unique_folder_name,
            extracted_folder_name,
            evaluation_script,
        )
    except KeyError:
        message = (
            "There is no key for evaluation script in YAML file. "
            "Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for evaluation script file in extracted zip folder.
    if isfile(evaluation_script_path):
        with open(evaluation_script_path, "rb") as challenge_evaluation_script:
            challenge_evaluation_script_file = ContentFile(
                challenge_evaluation_script.read(), evaluation_script_path
            )
    else:
        message = (
            "No evaluation script is present in the zip file. "
            "Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for test annotation file path in yaml file.
    try:
        challenge_phases_data = yaml_file_data["challenge_phases"]
    except KeyError:
        message = (
            "No challenge phase key found. "
            "Please add challenge phases in YAML file and try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    for data in challenge_phases_data:
        test_annotation_file = data.get("test_annotation_file")
        if test_annotation_file:
            test_annotation_file_path = join(
                BASE_LOCATION,
                unique_folder_name,
                extracted_folder_name,
                test_annotation_file,
            )
            if not isfile(test_annotation_file_path):
                message = (
                    "No test annotation file found in zip file"
                    " for challenge phase '{}'. Please add it and "
                    " then try again!".format(data["name"])
                )
                response_data = {"error": message}
                return Response(
                    response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                )
        else:
            message = (
                "There is no key for test annotation file for"
                " challenge phase {} in yaml file. Please add it"
                " and then try again!".format(data["name"])
            )
            response_data = {"error": message}
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        if data.get("is_submission_public") and data.get(
            "is_restricted_to_select_one_submission"
        ):
            message = (
                "is_submission_public can't be 'True' for for challenge phase '{}'"
                " with is_restricted_to_select_one_submission 'True'. "
                " Please change is_submission_public to 'False'"
                " then try again!".format(data["name"])
            )
            response_data = {"error": message}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # To ensure that the schema for submission meta attributes is valid.
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
                                message = "Please include at least one option in attribute for challenge_phase {}".format(
                                    data["id"]
                                )
                                response_data = {"error": message}
                                return Response(
                                    response_data,
                                    status=status.HTTP_406_NOT_ACCEPTABLE,
                                )
                else:
                    missing_keys_string = ", ".join(missing_keys)
                    message = "Please enter the following to the submission meta attribute in phase {}: {}.".format(
                        data["id"], missing_keys_string
                    )
                    response_data = {"error": message}
                    return Response(
                        response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                    )

        if data.get("default_submission_meta_attributes"):
            for attribute in data["default_submission_meta_attributes"]:
                keys = ["name", "is_visible"]
                missing_keys = get_missing_keys_from_dict(attribute, keys)

                if len(missing_keys) == 0:
                    valid_attributes = ["method_name", "method_description", "project_url", "publication_url"]
                    if not attribute["name"] in valid_attributes:
                        message = "Default meta attribute: {} in phase: {} does not exist!".format(
                            attribute["name"], data["id"]
                        )
                        response_data = {"error": message}
                        return Response(
                            response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                        )
                else:
                    missing_keys_string = ", ".join(missing_keys)
                    message = "Please enter the following to the default submission meta attribute in phase {}: {}.".format(
                        data["id"], missing_keys_string
                    )
                    response_data = {"error": message}
                    return Response(
                        response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                    )

    # Check for challenge image in yaml file.
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

    # check for challenge description file
    try:
        challenge_description_file_path = join(
            BASE_LOCATION,
            unique_folder_name,
            extracted_folder_name,
            yaml_file_data["description"],
        )
        if challenge_description_file_path.endswith(".html") and isfile(
            challenge_description_file_path
        ):
            yaml_file_data["description"] = get_file_content(
                challenge_description_file_path, "rb"
            ).decode("utf-8")
        else:
            yaml_file_data["description"] = None
    except KeyError:
        message = (
            "There is no key for description. "
            "Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

    # check for evaluation details file
    try:
        challenge_evaluation_details_file_path = join(
            BASE_LOCATION,
            unique_folder_name,
            extracted_folder_name,
            yaml_file_data["evaluation_details"],
        )

        if challenge_evaluation_details_file_path.endswith(".html") and isfile(
            challenge_evaluation_details_file_path
        ):
            yaml_file_data["evaluation_details"] = get_file_content(
                challenge_evaluation_details_file_path, "rb"
            ).decode("utf-8")
        else:
            yaml_file_data["evaluation_details"] = None
    except KeyError:
        message = (
            "There is no key for evalutaion details. "
            "Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

    # check for terms and conditions file
    try:
        challenge_terms_and_cond_file_path = join(
            BASE_LOCATION,
            unique_folder_name,
            extracted_folder_name,
            yaml_file_data["terms_and_conditions"],
        )
        if challenge_terms_and_cond_file_path.endswith(".html") and isfile(
            challenge_terms_and_cond_file_path
        ):
            yaml_file_data["terms_and_conditions"] = get_file_content(
                challenge_terms_and_cond_file_path, "rb"
            ).decode("utf-8")
        else:
            yaml_file_data["terms_and_conditions"] = None
    except KeyError:
        message = (
            "There is no key for terms and conditions. "
            "Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

    # Check for submission guidelines file
    try:
        submission_guidelines_file_path = join(
            BASE_LOCATION,
            unique_folder_name,
            extracted_folder_name,
            yaml_file_data["submission_guidelines"],
        )
        if submission_guidelines_file_path.endswith(".html") and isfile(
            submission_guidelines_file_path
        ):
            yaml_file_data["submission_guidelines"] = get_file_content(
                submission_guidelines_file_path, "rb"
            ).decode("utf-8")
        else:
            yaml_file_data["submission_guidelines"] = None
    except KeyError:
        message = (
            "There is no key for submission guidelines. "
            "Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

    # Check for leaderboard schema in YAML file
    leaderboard_schema = yaml_file_data.get("leaderboard")
    """
    Format of leaderboard data is:
    [
      {
        'id': 1,
        'schema': {
          'default_order_by': 'bleu',
          'labels': ['bleu']
        }
      }
    ]
    """
    if leaderboard_schema:
        if "schema" not in leaderboard_schema[0]:
            message = (
                "There is no leaderboard schema in the YAML "
                "configuration file. Please add it and then try again!"
            )
            response_data = {"error": message}
            return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)
        if "default_order_by" not in leaderboard_schema[0].get("schema"):
            message = (
                "There is no 'default_order_by' key in leaderboard "
                "schema. Please add it and then try again!"
            )
            response_data = {"error": message}
            return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)
        if "labels" not in leaderboard_schema[0].get("schema"):
            message = (
                "There is no 'labels' key in leaderboard "
                "schema. Please add it and then try again!"
            )
            response_data = {"error": message}
            return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)
    else:
        message = (
            "There is no key 'leaderboard' "
            "in the YAML file. Please add it and then try again!"
        )
        response_data = {"error": message}
        return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

    challenge_fields = [
        "title",
        "description",
        "start_date",
        "start_date",
        "end_date",
    ]
    challenge_phase_fields = ["name", "start_date", "end_date"]
    if is_challenge_template:
        for field in challenge_fields:
            yaml_file_data[field] = challenge_data_from_hosts.get(field)

        # Mapping the challenge phase data to that in yaml_file_data
        challenge_phases = yaml_file_data["challenge_phases"]
        challenge_phases_from_hosts = challenge_data_from_hosts.get(
            "challenge_phases"
        )
        challenge_phases_from_hosts = json.loads(challenge_phases_from_hosts)

        for challenge_phase_data, challenge_phase_data_from_hosts in zip(
            challenge_phases, challenge_phases_from_hosts
        ):
            for field in challenge_phase_fields:
                challenge_phase_data[
                    field
                ] = challenge_phase_data_from_hosts.get(field)

    try:
        with transaction.atomic():
            serializer = ZipChallengeSerializer(
                data=yaml_file_data,
                context={
                    "request": request,
                    "challenge_host_team": challenge_host_team,
                    "image": challenge_image_file,
                    "evaluation_script": challenge_evaluation_script_file,
                },
            )
            if serializer.is_valid():
                serializer.save()
                challenge = serializer.instance
                queue_name = get_queue_name(challenge.title, challenge.pk)
                challenge.queue = queue_name
                challenge.save()
            else:
                response_data = serializer.errors
                # transaction.set_rollback(True)
                # return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

            # Create Leaderboard
            yaml_file_data_of_leaderboard = yaml_file_data["leaderboard"]
            leaderboard_ids = {}
            for data in yaml_file_data_of_leaderboard:
                serializer = LeaderboardSerializer(
                    data=data, context={"config_id": data["id"]}
                )
                if serializer.is_valid():
                    serializer.save()
                    leaderboard_ids[str(data["id"])] = serializer.instance.pk
                else:
                    response_data = serializer.errors

            # Create Challenge Phase
            challenge_phase_ids = {}
            for data in challenge_phases_data:
                # Check for challenge phase description file
                phase_description_file_path = join(
                    BASE_LOCATION,
                    unique_folder_name,
                    extracted_folder_name,
                    data["description"],
                )
                if phase_description_file_path.endswith(".html") and isfile(
                    phase_description_file_path
                ):
                    data["description"] = get_file_content(
                        phase_description_file_path, "rb"
                    ).decode("utf-8")
                else:
                    data["description"] = None

                data["slug"] = "{}-{}-{}".format(
                    challenge.title.split(" ")[0].lower(),
                    data["codename"].replace(" ", "-").lower(),
                    challenge.pk,
                )[:198]
                test_annotation_file = data.get("test_annotation_file")
                if test_annotation_file:
                    test_annotation_file_path = join(
                        BASE_LOCATION,
                        unique_folder_name,
                        extracted_folder_name,
                        test_annotation_file,
                    )
                    if isfile(test_annotation_file_path):
                        with open(
                            test_annotation_file_path, "rb"
                        ) as test_annotation_file:
                            challenge_test_annotation_file = ContentFile(
                                test_annotation_file.read(),
                                test_annotation_file_path,
                            )
                if data.get("max_submissions_per_month", None) is None:
                    data["max_submissions_per_month"] = data.get(
                        "max_submissions", None
                    )

                if test_annotation_file:
                    serializer = ChallengePhaseCreateSerializer(
                        data=data,
                        context={
                            "challenge": challenge,
                            "test_annotation": challenge_test_annotation_file,
                            "config_id": data["id"],
                        },
                    )
                else:
                    # This is when the host wants to upload the annotation file later through CLI
                    serializer = ChallengePhaseCreateSerializer(
                        data=data,
                        context={
                            "challenge": challenge,
                            "config_id": data["id"],
                        },
                    )
                if serializer.is_valid():
                    serializer.save()
                    challenge_phase_ids[
                        str(data["id"])
                    ] = serializer.instance.pk
                else:
                    response_data = serializer.errors

            # Create Dataset Splits
            yaml_file_data_of_dataset_split = yaml_file_data["dataset_splits"]
            dataset_split_ids = {}
            for data in yaml_file_data_of_dataset_split:
                serializer = DatasetSplitSerializer(
                    data=data, context={"config_id": data["id"]}
                )
                if serializer.is_valid():
                    serializer.save()
                    dataset_split_ids[str(data["id"])] = serializer.instance.pk
                else:
                    # Return error when dataset split name is not unique.
                    response_data = serializer.errors

            # Create Challenge Phase Splits
            try:
                challenge_phase_splits_data = yaml_file_data[
                    "challenge_phase_splits"
                ]
            except KeyError:
                message = (
                    "There is no key for challenge phase splits. "
                    "Please add it and then try again!"
                )
                response_data = {"error": message}
                return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)

            for data in challenge_phase_splits_data:
                challenge_phase = challenge_phase_ids[
                    str(data["challenge_phase_id"])
                ]
                leaderboard = leaderboard_ids[str(data["leaderboard_id"])]
                dataset_split = dataset_split_ids[
                    str(data["dataset_split_id"])
                ]
                visibility = data["visibility"]

                data = {
                    "challenge_phase": challenge_phase,
                    "leaderboard": leaderboard,
                    "dataset_split": dataset_split,
                    "visibility": visibility,
                }

                serializer = ZipChallengePhaseSplitSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    response_data = serializer.errors

        zip_config = ChallengeConfiguration.objects.get(
            pk=uploaded_zip_file.pk
        )
        if zip_config:
            emails = challenge_host_team.get_all_challenge_host_email()
            if not challenge.is_docker_based:
                # Add the Challenge Host as a test participant.
                team_name = "Host_{}_Team".format(random.randint(1, 100000))
                participant_host_team = ParticipantTeam(
                    team_name=team_name,
                    created_by=challenge_host_team.created_by,
                )
                participant_host_team.save()
                for email in emails:
                    user = User.objects.get(email=email)
                    host = Participant(
                        user=user,
                        status=Participant.ACCEPTED,
                        team=participant_host_team,
                    )
                    host.save()
                challenge.participant_teams.add(participant_host_team)

            zip_config.challenge = challenge
            zip_config.save()

            if not settings.DEBUG:
                message = {
                    "text": "A *new challenge* has been uploaded to EvalAI.",
                    "fields": [
                        {
                            "title": "Email",
                            "value": request.user.email,
                            "short": False,
                        },
                        {
                            "title": "Challenge title",
                            "value": challenge.title,
                            "short": False,
                        },
                    ],
                }
                send_slack_notification(message=message)

            template_data = get_challenge_template_data(zip_config.challenge)
            if not challenge.is_docker_based and challenge.inform_hosts and not challenge.remote_evaluation:
                try:
                    response = start_workers([zip_config.challenge])
                    count, failures = response["count"], response["failures"]
                    logging.info("Total worker start count is {} and failures are: {}".format(count, failures))
                    if count:
                        logging.info("{} workers started successfully".format(count))
                        template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get(
                            "WORKER_START_EMAIL"
                        )
                        send_emails(emails, template_id, template_data)
                except Exception:
                    logger.exception(
                        "Failed to start workers for challenge {}".format(zip_config.challenge.pk)
                    )

            response_data = {
                "success": "Challenge {} has been created successfully and"
                " sent for review to EvalAI Admin.".format(challenge.title)
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

    except:  # noqa: E722
        try:
            if response_data:
                response_data = {"error": response_data}
                return Response(
                    response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                )
        except:  # noqa: E722
            response_data = {
                "error": "Error in creating challenge. Please check the yaml configuration!"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        finally:
            try:
                shutil.rmtree(BASE_LOCATION)
                logger.info("Zip folder is removed")
            except:  # noqa: E722
                logger.exception(
                    "Zip folder for challenge {} is not removed from {} location".format(
                        challenge.pk, BASE_LOCATION
                    )
                )


@swagger_auto_schema(
    methods=["get"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        ),
        openapi.Parameter(
            name="challenge_phase_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge Phase ID",
            required=True,
        ),
    ],
    operation_id="get_all_submissions_for_a_challenge",
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Count of submissions",
                    ),
                    "next": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="URL of next page of results",
                    ),
                    "previous": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="URL of previous page of results",
                    ),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description="Array of results object",
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="Submission ID",
                                ),
                                "participant_team": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Participant Team Name",
                                ),
                                "challenge_phase": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Challenge Phase name",
                                ),
                                "created_by": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Username of user who created the submission",
                                ),
                                "status": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Status of the submission",
                                ),
                                "is_public": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Shows if the submission is public or not",
                                ),
                                "is_flagged": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Shows if the submission is flagged or not",
                                ),
                                "submission_number": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="Count of submissions done by a team",
                                ),
                                "submitted_at": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Timestamp when submission was submitted",
                                ),
                                "execution_time": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Execution time of the submission in seconds",
                                ),
                                "input_file": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="URL of the file submitted by user",
                                ),
                                "stdout_file": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="URL of the stdout file generated after evaluating submission",
                                ),
                                "stderr_file": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="URL of the stderr file generated after evaluating submission only available when the submission fails",
                                ),
                                "submission_result_file": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="URL of the result file generated after successfully evaluating submission",
                                ),
                                "submission_metadata_file": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="URL of the metadata file generated after successfully evaluating submission",
                                ),
                                "participant_team_members_email_ids": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Array of the participant team members email ID's",
                                ),
                                "participant_team_members_affiliations": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Array of the participant team members affiliations",
                                ),
                                "created_at": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Timestamp when the submission was created",
                                ),
                                "method_name": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Name of the method used by the participant team",
                                ),
                                "participant_team_members": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Array of participant team members name and email",
                                ),
                            },
                        ),
                    ),
                },
            ),
        )
    },
)
@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_all_submissions_of_challenge(
    request, challenge_pk, challenge_phase_pk
):
    """
    Returns all the submissions for a particular challenge
    """
    # To check for the corresponding challenge from challenge_pk.
    challenge = get_challenge_model(challenge_pk)

    # To check for the corresponding challenge phase from the challenge_phase_pk and challenge.
    try:
        challenge_phase = ChallengePhase.objects.get(
            pk=challenge_phase_pk, challenge=challenge
        )
    except ChallengePhase.DoesNotExist:
        response_data = {
            "error": "Challenge Phase {} does not exist".format(
                challenge_phase_pk
            )
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    # To check for the user as a host of the challenge from the request and challenge_pk.
    if is_user_a_host_of_challenge(
        user=request.user, challenge_pk=challenge_pk
    ):

        # Filter submissions on the basis of challenge for host for now. Later on, the support for query
        # parameters like challenge phase, date is to be added.
        submissions = Submission.objects.filter(
            challenge_phase=challenge_phase, ignore_submission=False
        ).order_by("-submitted_at")
        filtered_submissions = SubmissionFilter(
            request.GET, queryset=submissions
        )
        paginator, result_page = paginated_queryset(
            filtered_submissions.qs, request
        )
        serializer = ChallengeSubmissionManagementSerializer(
            result_page, many=True, context={"request": request}
        )
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    # To check for the user as a participant of the challenge from the request and challenge_pk.
    elif has_user_participated_in_challenge(
        user=request.user, challenge_id=challenge_pk
    ):

        # get participant team object for the user for a particular challenge.
        participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_pk
        )

        # Filter submissions on the basis of challenge phase for a participant.
        submissions = Submission.objects.filter(
            participant_team=participant_team_pk,
            challenge_phase=challenge_phase,
        ).order_by("-submitted_at")
        paginator, result_page = paginated_queryset(submissions, request)
        serializer = SubmissionSerializer(
            result_page, many=True, context={"request": request}
        )
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    # when user is neither host not participant of the challenge.
    else:
        response_data = {
            "error": "You are neither host nor participant of the challenge!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def download_all_submissions(
    request, challenge_pk, challenge_phase_pk, file_type
):

    # To check for the corresponding challenge from challenge_pk.
    challenge = get_challenge_model(challenge_pk)

    # To check for the corresponding challenge phase from the challenge_phase_pk and challenge.
    try:
        challenge_phase = ChallengePhase.objects.get(
            pk=challenge_phase_pk, challenge=challenge
        )
    except ChallengePhase.DoesNotExist:
        response_data = {
            "error": "Challenge Phase {} does not exist".format(
                challenge_phase_pk
            )
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        if file_type == "csv":
            if is_user_a_host_of_challenge(
                user=request.user, challenge_pk=challenge_pk
            ):
                submissions = Submission.objects.filter(
                    challenge_phase__challenge=challenge
                ).order_by("-submitted_at")
                submissions = ChallengeSubmissionManagementSerializer(
                    submissions, many=True, context={"request": request}
                )
                response = HttpResponse(content_type="text/csv")
                response[
                    "Content-Disposition"
                ] = "attachment; filename=all_submissions.csv"
                writer = csv.writer(response)
                writer.writerow(
                    [
                        "id",
                        "Team Name",
                        "Team Members",
                        "Team Members Email Id",
                        "Team Members Affiliaton",
                        "Challenge Phase",
                        "Status",
                        "Created By",
                        "Execution Time(sec.)",
                        "Submission Number",
                        "Submitted File",
                        "Stdout File",
                        "Stderr File",
                        "Submitted At",
                        "Submission Result File",
                        "Submission Metadata File",
                    ]
                )
                for submission in submissions.data:
                    writer.writerow(
                        [
                            submission["id"],
                            submission["participant_team"],
                            ",".join(
                                username["username"]
                                for username in submission[
                                    "participant_team_members"
                                ]
                            ),
                            ",".join(
                                email["email"]
                                for email in submission[
                                    "participant_team_members"
                                ]
                            ),
                            ",".join(
                                affiliation
                                for affiliation in submission[
                                    "participant_team_members_affiliations"
                                ]
                            ),
                            submission["challenge_phase"],
                            submission["status"],
                            submission["created_by"],
                            submission["execution_time"],
                            submission["submission_number"],
                            submission["input_file"],
                            submission["stdout_file"],
                            submission["stderr_file"],
                            submission["created_at"],
                            submission["submission_result_file"],
                            submission["submission_metadata_file"],
                        ]
                    )
                return response

            elif has_user_participated_in_challenge(
                user=request.user, challenge_id=challenge_pk
            ):

                # get participant team object for the user for a particular challenge.
                participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
                    request.user, challenge_pk
                )

                # Filter submissions on the basis of challenge phase for a participant.
                submissions = Submission.objects.filter(
                    participant_team=participant_team_pk,
                    challenge_phase=challenge_phase,
                ).order_by("-submitted_at")
                submissions = ChallengeSubmissionManagementSerializer(
                    submissions, many=True, context={"request": request}
                )
                response = HttpResponse(content_type="text/csv")
                response[
                    "Content-Disposition"
                ] = "attachment; filename=all_submissions.csv"
                writer = csv.writer(response)
                writer.writerow(
                    [
                        "Team Name",
                        "Method Name",
                        "Status",
                        "Execution Time(sec.)",
                        "Submitted File",
                        "Result File",
                        "Stdout File",
                        "Stderr File",
                        "Submitted At",
                    ]
                )
                for submission in submissions.data:
                    writer.writerow(
                        [
                            submission["participant_team"],
                            submission["method_name"],
                            submission["status"],
                            submission["execution_time"],
                            submission["input_file"],
                            submission["submission_result_file"],
                            submission["stdout_file"],
                            submission["stderr_file"],
                            submission["created_at"],
                        ]
                    )
                return response
            else:
                response_data = {
                    "error": "You are neither host nor participant of the challenge!"
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            response_data = {"error": "The file type requested is not valid!"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "POST":
        if file_type == "csv":
            if is_user_a_host_of_challenge(
                user=request.user, challenge_pk=challenge_pk
            ):
                fields_to_export = {
                    "participant_team": "Team Name",
                    "participant_team_members": "Team Members",
                    "participant_team_members_email": "Team Members Email Id",
                    "participant_team_members_affiliation": "Team Members Affiliation",
                    "challenge_phase": "Challenge Phase",
                    "status": "Status",
                    "created_by": "Created By",
                    "execution_time": "Execution Time(sec.)",
                    "submission_number": "Submission Number",
                    "input_file": "Submitted File",
                    "stdout_file": "Stdout File",
                    "stderr_file": "Stderr File",
                    "created_at": "Submitted At (mm/dd/yyyy hh:mm:ss)",
                    "submission_result_file": "Submission Result File",
                    "submission_metadata_file": "Submission Metadata File",
                }
                submissions = Submission.objects.filter(
                    challenge_phase__challenge=challenge
                ).order_by("-submitted_at")
                submissions = ChallengeSubmissionManagementSerializer(
                    submissions, many=True, context={"request": request}
                )
                response = HttpResponse(content_type="text/csv")
                response[
                    "Content-Disposition"
                ] = "attachment; filename=all_submissions.csv"
                writer = csv.writer(response)
                fields = [fields_to_export[field] for field in request.data]
                fields.insert(0, "id")
                writer.writerow(fields)
                for submission in submissions.data:
                    row = [submission["id"]]
                    for field in request.data:
                        if field == "participant_team_members":
                            row.append(
                                ",".join(
                                    username["username"]
                                    for username in submission[
                                        "participant_team_members"
                                    ]
                                )
                            )
                        elif field == "participant_team_members_email":
                            row.append(
                                ",".join(
                                    email["email"]
                                    for email in submission[
                                        "participant_team_members"
                                    ]
                                )
                            )
                        elif field == "participant_team_members_affiliation":
                            row.append(
                                ",".join(
                                    affiliation
                                    for affiliation in submission[
                                        "participant_team_members_affiliations"
                                    ]
                                )
                            )
                        elif field == "created_at":
                            row.append(
                                submission["created_at"].strftime(
                                    "%m/%d/%Y %H:%M:%S"
                                )
                            )
                        else:
                            row.append(submission[field])
                    writer.writerow(row)
                return response

            else:
                response_data = {
                    "error": "Sorry, you do not belong to this Host Team!"
                }
                return Response(
                    response_data, status=status.HTTP_401_UNAUTHORIZED
                )

        else:
            response_data = {"error": "The file type requested is not valid!"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_leaderboard(request):
    """
    Creates a leaderboard
    """
    serializer = LeaderboardSerializer(
        data=request.data, many=True, allow_empty=False
    )
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_or_update_leaderboard(request, leaderboard_pk):
    """
    Returns or Updates a leaderboard
    """
    leaderboard = get_leaderboard_model(leaderboard_pk)

    if request.method == "PATCH":
        serializer = LeaderboardSerializer(
            leaderboard, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        serializer = LeaderboardSerializer(leaderboard)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_dataset_split(request):
    """
    Creates a dataset split
    """
    serializer = DatasetSplitSerializer(
        data=request.data, many=True, allow_empty=False
    )
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        response_data = serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_or_update_dataset_split(request, dataset_split_pk):
    """
    Returns or Updates a dataset split
    """
    dataset_split = get_dataset_split_model(dataset_split_pk)
    if request.method == "PATCH":
        serializer = DatasetSplitSerializer(
            dataset_split, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = serializer.errors
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        serializer = DatasetSplitSerializer(dataset_split)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_challenge_phase_split(request):
    """
    Create Challenge Phase Split
    """
    serializer = ZipChallengePhaseSplitSerializer(
        data=request.data, many=True, allow_empty=False
    )
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        response_data = serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_or_update_challenge_phase_split(request, challenge_phase_split_pk):
    """
    Returns or Updates challenge phase split
    """
    challenge_phase_split = get_challenge_phase_split_model(
        challenge_phase_split_pk
    )

    if request.method == "PATCH":
        serializer = ZipChallengePhaseSplitSerializer(
            challenge_phase_split, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        serializer = ZipChallengePhaseSplitSerializer(challenge_phase_split)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def star_challenge(request, challenge_pk):
    """
    API endpoint for starring and unstarring
    a challenge.
    """
    challenge = get_challenge_model(challenge_pk)

    if request.method == "POST":
        try:
            starred_challenge = StarChallenge.objects.get(
                user=request.user.pk, challenge=challenge
            )
            starred_challenge.is_starred = not starred_challenge.is_starred
            starred_challenge.save()
            serializer = StarChallengeSerializer(starred_challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except StarChallenge.DoesNotExist:
            serializer = StarChallengeSerializer(
                data=request.data,
                context={
                    "request": request,
                    "challenge": challenge,
                    "is_starred": True,
                },
            )
            if serializer.is_valid():
                serializer.save()
                response_data = serializer.data
                return Response(response_data, status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    if request.method == "GET":
        try:
            starred_challenge = StarChallenge.objects.get(
                user=request.user.pk, challenge=challenge
            )
            serializer = StarChallengeSerializer(starred_challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except StarChallenge.DoesNotExist:
            starred_challenge = StarChallenge.objects.filter(
                challenge=challenge
            )
            if not starred_challenge:
                response_data = {"is_starred": False, "count": 0}
                return Response(response_data, status=status.HTTP_200_OK)

            serializer = StarChallengeSerializer(starred_challenge, many=True)
            response_data = {
                "is_starred": False,
                "count": serializer.data[0]["count"],
            }
            return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_broker_urls(request):
    """
    Returns:
        Queue name of approved challenges
    """
    is_active = request.data.get("is_active", False)

    q_params = {"approved_by_admin": True}
    if is_active:
        q_params["start_date__lt"] = timezone.now()
        q_params["end_date__gt"] = timezone.now()

    if not request.user.is_superuser:
        response_data = {
            "error": "You are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    else:
        challenges = Challenge.objects.filter(**q_params)
        response_data = challenges.values_list("queue", flat=True)
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_broker_url_by_challenge_pk(request, challenge_pk):
    """
    Returns:
        Queue name of challenge with challenge pk
    """
    if not request.user.is_superuser:
        response_data = {
            "error": "You are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    else:
        try:
            challenge = Challenge.objects.get(
                pk=challenge_pk, approved_by_admin=True
            )
        except Challenge.DoesNotExist:
            response_data = {
                "error": "Challenge {} does not exist".format(challenge_pk)
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        response_data = [challenge.queue]
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_aws_credentials_for_participant_team(request, phase_pk):
    """
        Endpoint to generate AWS Credentails for CLI
        Args:
            - challenge: Challenge model
            - participant_team: Participant Team Model
        Returns:
            - JSON: {
                    "federated_user"
                    "docker_repository_uri"
                }
        Raises:
            - BadRequestException 400
                - When participant_team has not participanted in challenge
                - When Challenge is not Docker based
    """
    challenge_phase = get_challenge_phase_model(phase_pk)
    challenge = challenge_phase.challenge
    participant_team = get_participant_team_of_user_for_a_challenge(
        request.user, challenge.pk
    )
    if not challenge.is_docker_based:
        response_data = {
            "error": "Sorry, this is not a docker based challenge."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if participant_team is None:
        response_data = {
            "error": "You have not participated in this challenge."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    data = get_aws_credentials_for_submission(challenge, participant_team)
    response_data = {"success": data}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def invite_users_to_challenge(request, challenge_pk):

    challenge = get_challenge_model(challenge_pk)

    if not challenge.is_active or not challenge.approved_by_admin:
        response_data = {"error": "Sorry, the challenge is not active"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        challenge_host = ChallengeHost.objects.get(user=request.user)
    except ChallengeHost.DoesNotExist:
        response_data = {"error": "You're not a challenge host"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "You're not authorized to invite a user in {}".format(
                challenge.title
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    users_email = request.data.get("emails")

    if not users_email:
        response_data = {"error": "Users email can't be blank"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        users_email = eval(users_email)
    except Exception:
        response_data = {"error": "Invalid format for users email"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    invalid_emails = []
    valid_emails = []
    for email in users_email:
        try:
            invited_user = UserInvitation.objects.get(
                email=email, challenge=challenge.pk
            )
            invitation_key = invited_user.invitation_key
        except UserInvitation.DoesNotExist:
            invitation_key = uuid.uuid4()
            invitation_status = UserInvitation.PENDING
            data = {
                "email": email,
                "invitation_key": str(invitation_key),
                "status": invitation_status,
                "challenge": challenge.pk,
                "invited_by": challenge_host.pk,
            }
            serializer = UserInvitationSerializer(data=data, partial=True)
            if serializer.is_valid():
                user, created = User.objects.get_or_create(
                    username=email, email=email
                )
                if created:
                    EmailAddress.objects.create(
                        user=user, email=email, primary=True, verified=True
                    )
                data["user"] = user.pk
                valid_emails.append(data)
            else:
                invalid_emails.append(email)

        sender_email = settings.CLOUDCV_TEAM_EMAIL
        hostname = get_url_from_hostname(settings.HOSTNAME)
        url = "{}/accept-invitation/{}/".format(hostname, invitation_key)
        template_data = {"title": challenge.title, "url": url}
        if challenge.image:
            template_data["image"] = challenge.image.url
        template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get(
            "CHALLENGE_INVITATION"
        )

        if email not in invalid_emails:
            send_email(sender_email, email, template_id, template_data)

    if valid_emails:
        serializer = UserInvitationSerializer(data=valid_emails, many=True)
        if serializer.is_valid():
            serializer.save()

    if len(users_email) == len(invalid_emails):
        response_data = {"error": "Please enter correct email addresses"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    response_data = {
        "success": "Invitations sent successfully",
        "invalid_emails": invalid_emails,
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes(())
def accept_challenge_invitation(request, invitation_key):
    try:
        invitation = UserInvitation.objects.get(invitation_key=invitation_key)
    except UserInvitation.DoesNotExist:
        response_data = {
            "error": "The invitation with key {} doesn't exist".format(
                invitation_key
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        serializer = UserInvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PATCH":
        serializer = UserDetailsSerializer(
            invitation.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            data = {"password": make_password(serializer.data.get("password"))}
            serializer = UserDetailsSerializer(
                invitation.user, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
            data = {"status": UserInvitation.ACCEPTED}
            serializer = UserInvitationSerializer(
                invitation, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_by_queue_name(request, queue_name):
    """
    API endpoint to fetch the challenge details by using pk
    Arguments:
        queue_name -- Challenge queue name for which the challenge deatils are fetched
    Returns:
        Response Object -- An object containing challenge details
    """

    try:
        challenge = Challenge.objects.get(queue=queue_name)
    except Challenge.DoesNotExist:
        response_data = {
            "error": "Challenge with queue name {} does not exist".format(
                queue_name
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to access this challenge."
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    serializer = ZipChallengeSerializer(
        challenge, context={"request": request}
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_phases_by_challenge_pk(request, challenge_pk):
    """
    API endpoint to fetch all challenge phase details corresponding to a challenge using challenge pk
    Arguments:
        challenge_pk -- Challenge Id for which the details is to be fetched
    Returns:
        Response Object -- An object containing all challenge phases for the challenge
    """
    challenge = get_challenge_model(challenge_pk)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to access these challenge phases."
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    challenge_phases = ChallengePhase.objects.filter(challenge=challenge_pk)
    serializer = ChallengePhaseCreateSerializer(
        challenge_phases, context={"request": request}, many=True
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def get_challenge_phase_by_pk(request, pk):
    """
    Returns a particular challenge phase details by pk
    """
    challenge_phase = get_challenge_phase_model(pk)
    serializer = ChallengePhaseSerializer(
        challenge_phase, context={"request": request}
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def get_challenge_phase_by_slug(request, slug):
    """
    Returns a particular challenge phase details by pk
    """
    try:
        challenge_phase = ChallengePhase.objects.get(slug=slug)
    except ChallengePhase.DoesNotExist:
        response_data = {
            "error": "Challenge phase with slug {} does not exist".format(slug)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    serializer = ChallengePhaseSerializer(challenge_phase)
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_phase_environment_url(request, slug):
    """
    Returns environment image url and tag required for RL challenge evaluation
    """
    try:
        challenge_phase = ChallengePhase.objects.get(slug=slug)
    except ChallengePhase.DoesNotExist:
        response_data = {
            "error": "Challenge phase with slug {} does not exist".format(slug)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    challenge = get_challenge_model(challenge_phase.challenge.pk)
    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to access test environment URL."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    if not challenge.is_docker_based:
        response_data = {
            "error": "The challenge doesn't require uploading Docker images, hence no test environment URL."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    response_data = {"environment_url": challenge_phase.environment_url}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_evaluation_cluster_details(request, challenge_pk):
    """API to get challenge evaluation cluster details for a challenge

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {int} -- The challenge pk for which the cluster details are required

    Returns:
        Response object -- Response object with appropriate response code (200/400/403/404)
    """
    challenge = get_challenge_model(challenge_pk)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to access evaluation cluster details."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not challenge.is_docker_based:
        response_data = {
            "error": "The challenge doesn't require uploading Docker images, hence no evaluation cluster details."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        challenge_evaluation_cluster = ChallengeEvaluationCluster.objects.get(
            challenge=challenge
        )
    except ChallengeEvaluationCluster.DoesNotExist:
        response_data = {
            "error": "Challenge evaluation cluster for the challenge with pk {} does not exist".format(
                challenge.pk
            )
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    serializer = ChallengeEvaluationClusterSerializer(
        challenge_evaluation_cluster, context={"request": request}
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def validate_challenge_config(request, challenge_host_team_pk):
    challenge_host_team = get_challenge_host_team_model(challenge_host_team_pk)

    response_data = {}

    BASE_LOCATION = tempfile.mkdtemp()
    unique_folder_name = get_unique_alpha_numeric_key(10)
    CHALLENGE_ZIP_DOWNLOAD_LOCATION = join(
        BASE_LOCATION, "{}.zip".format(unique_folder_name)
    )

    data = request.data
    challenge_config_serializer = ChallengeConfigSerializer(
        data=data, context={"request": request}
    )
    if challenge_config_serializer.is_valid():
        challenge_config_serializer.save()
        uploaded_zip_file_path = challenge_config_serializer.data[
            "zip_configuration"
        ]
    else:
        response_data["error"] = challenge_config_serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    is_success, error_description = download_and_write_file(
        uploaded_zip_file_path, True, CHALLENGE_ZIP_DOWNLOAD_LOCATION, "wb"
    )

    if not is_success:
        response_data["error"] = error_description
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Extract zip file
    try:
        zip_ref = extract_zip_file(
            CHALLENGE_ZIP_DOWNLOAD_LOCATION,
            "r",
            join(BASE_LOCATION, unique_folder_name),
        )
    except zipfile.BadZipfile:
        message = "The zip file contents cannot be extracted. Please check the format!"
        response_data["error"] = message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    error_messages, yaml_file_data, files = validate_challenge_config_util(
        request,
        challenge_host_team,
        BASE_LOCATION,
        unique_folder_name,
        zip_ref,
    )

    shutil.rmtree(BASE_LOCATION)

    if len(error_messages):
        response_data["error"] = "\n".join(error_messages)
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    else:
        message = "The challenge config has been validated successfully"
        response_data = {"Success": message}
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_worker_logs(request, challenge_pk):
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized to access the worker logs."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)
    response_data = []

    log_group_name = "challenge-pk-{}-workers".format(challenge.pk)
    log_stream_prefix = challenge.queue
    pattern = ""  # Empty string to get all logs including container logs.

    # This is to specify the time window for fetching logs: 15 minutes before from current time.
    timeframe = 15
    current_time = int(round(time.time() * 1000))
    start_time = current_time - (timeframe * 60000)
    end_time = current_time

    logs = get_logs_from_cloudwatch(
        log_group_name, log_stream_prefix, start_time, end_time, pattern
    )

    response_data = {"logs": logs}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def manage_worker(request, challenge_pk, action):
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized for access worker operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # make sure that the action is valid.
    if action not in ("start", "stop", "restart"):
        response_data = {
            "error": "The action {} is invalid for worker".format(action)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge = get_challenge_model(challenge_pk)

    response_data = {}

    if action == "start":
        response = start_workers([challenge])
    elif action == "stop":
        response = stop_workers([challenge])
    elif action == "restart":
        response = restart_workers([challenge])

    if response:
        count, failures = response["count"], response["failures"]
        logging.info(
            "Count is {} and failures are: {}".format(count, failures)
        )
        if count:
            response_data = {"action": "Success"}
        else:
            message = failures[0]["message"]
            response_data = {"action": "Failure", "error": message}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_annotation_file_presigned_url(request, challenge_phase_pk):
    """
    API to generate a presigned url to upload a test annotation file

    Arguments:
        request {HttpRequest} -- The request object
        challenge_phase_pk {int} -- Challenge phase primary key
    Returns:
         Response Object -- An object containing the presignd url, or an error message if some failure occurs
    """
    if settings.DEBUG or settings.TEST:
        response_data = {
            "error": "Sorry, this feature is not available in development or test environment."
        }
        return Response(response_data)
    # Check if the challenge phase exists or not
    try:
        challenge_phase = get_challenge_phase_model(challenge_phase_pk)
    except ChallengePhase.DoesNotExist:
        response_data = {"error": "Challenge Phase does not exist"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_a_host_of_challenge(
        request.user, challenge_phase.challenge.pk
    ):
        response_data = {
            "error": "Sorry, you are not authorized for uploading an annotation file."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    file_ext = os.path.splitext(request.data["file_name"])[-1]
    random_file_name = uuid.uuid4()

    if challenge_phase.test_annotation:
        file_key_on_s3 = "{}/{}".format(
            settings.MEDIAFILES_LOCATION, challenge_phase.test_annotation.name
        )
    else:
        # This file shall be replaced with the one uploaded through the presigned url from the CLI
        test_annotation_file = SimpleUploadedFile(
            "{}{}".format(random_file_name, file_ext),
            b"Dummy file content",
            content_type="text/plain",
        )
        serializer = ChallengePhaseCreateSerializer(
            challenge_phase,
            data={"test_annotation": test_annotation_file},
            context={"challenge": challenge_phase.challenge},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
        else:
            response_data = {"error": serializer.errors}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        challenge_phase = serializer.instance
        file_key_on_s3 = "{}/{}".format(
            settings.MEDIAFILES_LOCATION, challenge_phase.test_annotation.name
        )

    response = generate_presigned_url(
        file_key_on_s3, challenge_phase.challenge.pk
    )
    if response.get("error"):
        response_data = response
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    response_data = {"presigned_url": response.get("presigned_url")}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_or_update_github_challenge(request, challenge_host_team_pk):
    try:
        challenge_host_team = get_challenge_host_team_model(challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge_queryset = Challenge.objects.filter(
        github_repository=request.data["GITHUB_REPOSITORY"]
    )

    if challenge_queryset:
        challenge = challenge_queryset[0]
        if not is_user_a_host_of_challenge(request.user, challenge.pk):
            response_data = {
                "error": "Sorry, you are not a host for this challenge. Please check your user access token"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    response_data = {}

    BASE_LOCATION = tempfile.mkdtemp()
    unique_folder_name = get_unique_alpha_numeric_key(10)
    CHALLENGE_ZIP_DOWNLOAD_LOCATION = join(
        BASE_LOCATION, "{}.zip".format(unique_folder_name)
    )

    data = request.data
    challenge_config_serializer = ChallengeConfigSerializer(
        data=data, context={"request": request}
    )
    if challenge_config_serializer.is_valid():
        uploaded_zip_file = challenge_config_serializer.save()
        uploaded_zip_file_path = challenge_config_serializer.data[
            "zip_configuration"
        ]
    else:
        response_data["error"] = challenge_config_serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    is_success, error_description = download_and_write_file(
        uploaded_zip_file_path, True, CHALLENGE_ZIP_DOWNLOAD_LOCATION, "wb"
    )

    if not is_success:
        response_data["error"] = error_description
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Extract zip file
    try:
        zip_ref = extract_zip_file(
            CHALLENGE_ZIP_DOWNLOAD_LOCATION,
            "r",
            join(BASE_LOCATION, unique_folder_name),
        )
    except zipfile.BadZipfile:
        message = "The zip file contents cannot be extracted. Please check the format!"
        response_data["error"] = message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    error_messages, yaml_file_data, files = validate_challenge_config_util(
        request,
        challenge_host_team,
        BASE_LOCATION,
        unique_folder_name,
        zip_ref,
    )

    if not len(error_messages):
        if not challenge_queryset:
            try:
                with transaction.atomic():
                    serializer = ZipChallengeSerializer(
                        data=yaml_file_data,
                        context={
                            "request": request,
                            "challenge_host_team": challenge_host_team,
                            "image": files["challenge_image_file"],
                            "evaluation_script": files[
                                "challenge_evaluation_script_file"
                            ],
                            "github_repository": request.data[
                                "GITHUB_REPOSITORY"
                            ],
                        },
                    )
                    if serializer.is_valid():
                        serializer.save()
                    challenge = serializer.instance
                    queue_name = get_queue_name(challenge.title, challenge.pk)
                    challenge.queue = queue_name
                    challenge.save()

                    # Create Leaderboard
                    yaml_file_data_of_leaderboard = yaml_file_data[
                        "leaderboard"
                    ]
                    leaderboard_ids = {}
                    for data in yaml_file_data_of_leaderboard:
                        serializer = LeaderboardSerializer(
                            data=data, context={"config_id": data["id"]}
                        )
                        if serializer.is_valid():
                            serializer.save()
                        leaderboard_ids[
                            str(data["id"])
                        ] = serializer.instance.pk

                    # Create Challenge Phase
                    challenge_phase_ids = {}
                    challenge_phases_data = yaml_file_data["challenge_phases"]
                    for data, challenge_test_annotation_file in zip(
                        challenge_phases_data,
                        files["challenge_test_annotation_files"],
                    ):
                        data["slug"] = "{}-{}-{}".format(
                            challenge.title.split(" ")[0].lower(),
                            get_slug(data["codename"]),
                            challenge.pk,
                        )[:198]

                        if challenge_test_annotation_file:
                            serializer = ChallengePhaseCreateSerializer(
                                data=data,
                                context={
                                    "challenge": challenge,
                                    "test_annotation": challenge_test_annotation_file,
                                    "config_id": data["id"],
                                },
                            )
                        else:
                            # This is when the host wants to upload the annotation file later
                            serializer = ChallengePhaseCreateSerializer(
                                data=data,
                                context={
                                    "challenge": challenge,
                                    "config_id": data["id"],
                                },
                            )
                        if serializer.is_valid():
                            serializer.save()
                        challenge_phase_ids[
                            str(data["id"])
                        ] = serializer.instance.pk

                    # Create Dataset Splits
                    yaml_file_data_of_dataset_split = yaml_file_data[
                        "dataset_splits"
                    ]
                    dataset_split_ids = {}
                    for data in yaml_file_data_of_dataset_split:
                        serializer = DatasetSplitSerializer(
                            data=data, context={"config_id": data["id"]}
                        )
                        if serializer.is_valid():
                            serializer.save()
                        dataset_split_ids[
                            str(data["id"])
                        ] = serializer.instance.pk

                    # Create Challenge Phase Splits
                    challenge_phase_splits_data = yaml_file_data[
                        "challenge_phase_splits"
                    ]
                    for data in challenge_phase_splits_data:
                        challenge_phase = challenge_phase_ids[
                            str(data["challenge_phase_id"])
                        ]
                        leaderboard = leaderboard_ids[
                            str(data["leaderboard_id"])
                        ]
                        dataset_split = dataset_split_ids[
                            str(data["dataset_split_id"])
                        ]
                        visibility = data["visibility"]

                        data = {
                            "challenge_phase": challenge_phase,
                            "leaderboard": leaderboard,
                            "dataset_split": dataset_split,
                            "visibility": visibility,
                        }

                        serializer = ZipChallengePhaseSplitSerializer(
                            data=data,
                        )
                        if serializer.is_valid():
                            serializer.save()

                zip_config = ChallengeConfiguration.objects.get(
                    pk=uploaded_zip_file.pk
                )
                if zip_config:
                    if not challenge.is_docker_based:
                        # Add the Challenge Host as a test participant.
                        emails = (
                            challenge_host_team.get_all_challenge_host_email()
                        )
                        team_name = "Host_{}_Team".format(
                            random.randint(1, 100000)
                        )
                        participant_host_team = ParticipantTeam(
                            team_name=team_name,
                            created_by=challenge_host_team.created_by,
                        )
                        participant_host_team.save()
                        for email in emails:
                            user = User.objects.get(email=email)
                            host = Participant(
                                user=user,
                                status=Participant.ACCEPTED,
                                team=participant_host_team,
                            )
                            host.save()
                        challenge.participant_teams.add(participant_host_team)

                    zip_config.challenge = challenge
                    zip_config.save()

                    if not settings.DEBUG:
                        message = {
                            "text": "A *new challenge* has been created on EvalAI.",
                            "fields": [
                                {
                                    "title": "Email",
                                    "value": request.user.email,
                                    "short": False,
                                },
                                {
                                    "title": "Challenge title",
                                    "value": challenge.title,
                                    "short": False,
                                },
                            ],
                        }
                        send_slack_notification(message=message)

                    response_data = {
                        "Success": "Challenge {} has been created successfully and"
                        " sent for review to EvalAI Admin.".format(
                            challenge.title
                        )
                    }
                    return Response(
                        response_data, status=status.HTTP_201_CREATED
                    )

            except:  # noqa: E722
                response_data = {
                    "error": "Error in creating challenge. Please check the yaml configuration!"
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )
            finally:
                try:
                    shutil.rmtree(BASE_LOCATION)
                    logger.info("Zip folder is removed")
                except:  # noqa: E722
                    logger.exception(
                        "Zip folder for challenge {} is not removed from {} location".format(
                            challenge.pk, BASE_LOCATION
                        )
                    )

        else:
            # Updating ChallengeConfiguration object
            challenge_configuration = ChallengeConfiguration.objects.filter(
                challenge=challenge.pk
            ).first()
            serializer = ChallengeConfigSerializer(
                challenge_configuration,
                data=request.data,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()

            # Updating Challenge object
            serializer = ZipChallengeSerializer(
                challenge,
                data=yaml_file_data,
                context={
                    "request": request,
                    "challenge_host_team": challenge_host_team,
                    "image": files["challenge_image_file"],
                    "evaluation_script": files[
                        "challenge_evaluation_script_file"
                    ],
                },
            )
            if serializer.is_valid():
                serializer.save()
            challenge = serializer.instance

            # Updating Leaderboard object
            leaderboard_ids = {}
            yaml_file_data_of_leaderboard = yaml_file_data["leaderboard"]
            for data in yaml_file_data_of_leaderboard:
                challenge_phase_split_qs = ChallengePhaseSplit.objects.filter(
                    challenge_phase__challenge__pk=challenge.pk,
                    leaderboard__config_id=data["config_id"],
                )
                if challenge_phase_split_qs:
                    challenge_phase_split = challenge_phase_split_qs.first()
                    leaderboard = challenge_phase_split.leaderboard
                    serializer = LeaderboardSerializer(
                        leaderboard,
                        data=data,
                        context={"config_id": data["id"]},
                    )
                else:
                    serializer = LeaderboardSerializer(
                        data=data, context={"config_id": data["id"]}
                    )
                if serializer.is_valid():
                    serializer.save()
                    leaderboard_ids[str(data["id"])] = serializer.instance.pk

            # Updating ChallengePhase objects
            challenge_phase_ids = {}
            challenge_phases_data = yaml_file_data["challenge_phases"]
            for data, challenge_test_annotation_file in zip(
                challenge_phases_data, files["challenge_test_annotation_files"]
            ):
                challenge_phase = ChallengePhase.objects.filter(
                    challenge__pk=challenge.pk, config_id=data["id"]
                ).first()
                if challenge_test_annotation_file:
                    serializer = ChallengePhaseCreateSerializer(
                        challenge_phase,
                        data=data,
                        context={
                            "challenge": challenge,
                            "test_annotation": challenge_test_annotation_file,
                            "config_id": data["config_id"],
                        },
                    )
                else:
                    serializer = ChallengePhaseCreateSerializer(
                        challenge_phase,
                        data=data,
                        context={
                            "challenge": challenge,
                            "config_id": data["config_id"],
                        },
                    )
                if serializer.is_valid():
                    serializer.save()
                    challenge_phase_ids[
                        str(data["id"])
                    ] = serializer.instance.pk

            # Updating DatasetSplit objects
            yaml_file_data_of_dataset_split = yaml_file_data["dataset_splits"]
            dataset_split_ids = {}
            for data in yaml_file_data_of_dataset_split:
                challenge_phase_split_qs = ChallengePhaseSplit.objects.filter(
                    challenge_phase__challenge__pk=challenge.pk,
                    dataset_split__config_id=data["id"],
                )
                if challenge_phase_split_qs:
                    challenge_phase_split = challenge_phase_split_qs.first()
                    dataset_split = challenge_phase_split.dataset_split
                    serializer = DatasetSplitSerializer(
                        dataset_split,
                        data=data,
                        context={"config_id": data["id"]},
                    )
                else:
                    serializer = DatasetSplitSerializer(
                        data=data, context={"config_id": data["id"]}
                    )
                if serializer.is_valid():
                    serializer.save()
                    dataset_split_ids[str(data["id"])] = serializer.instance.pk

            # Update ChallengePhaseSplit objects
            challenge_phase_splits_data = yaml_file_data[
                "challenge_phase_splits"
            ]
            for data in challenge_phase_splits_data:
                challenge_phase = challenge_phase_ids[
                    str(data["challenge_phase_id"])
                ]
                leaderboard = leaderboard_ids[str(data["leaderboard_id"])]
                dataset_split = dataset_split_ids[
                    str(data["dataset_split_id"])
                ]
                visibility = data["visibility"]

                data = {
                    "challenge_phase": challenge_phase,
                    "leaderboard": leaderboard,
                    "dataset_split": dataset_split,
                    "visibility": visibility,
                }

                challenge_phase_split_qs = ChallengePhaseSplit.objects.filter(
                    challenge_phase__pk=challenge_phase,
                    dataset_split__pk=dataset_split,
                )
                if challenge_phase_split_qs:
                    challenge_phase_split = challenge_phase_split_qs.first()
                    serializer = ZipChallengePhaseSplitSerializer(
                        challenge_phase_split, data=data,
                    )
                else:
                    serializer = ZipChallengePhaseSplitSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()

            response_data = {
                "Success": "The challenge {} has been updated successfully".format(
                    challenge.title
                )
            }
            return Response(response_data, status=status.HTTP_200_OK)
    else:
        shutil.rmtree(BASE_LOCATION)
        logger.info("Challenge config validation failed. Zip folder removed")
        response_data["error"] = "\n".join(error_messages)
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_all_challenge_templates(request):
    q_params = {"is_active": True}
    challenges = ChallengeTemplate.objects.filter(**q_params).order_by("-pk")
    serializer = ChallengeTemplateSerializer(
        challenges, many=True, context={"request": request}
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)
