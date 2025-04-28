import csv
import json
import logging
import os
import random
import shutil
import tempfile
import time
import uuid
import zipfile
from datetime import datetime
from os.path import basename, isfile, join

import pytz
import requests
import yaml
from accounts.permissions import HasVerifiedEmail
from accounts.serializers import UserDetailsSerializer
from allauth.account.models import EmailAddress
from base.utils import (
    get_queue_name,
    get_slug,
    get_url_from_hostname,
    is_user_a_staff,
    paginated_queryset,
    send_email,
    send_slack_notification,
)
from challenges.challenge_config_utils import (
    download_and_write_file,
    extract_zip_file,
    validate_challenge_config_util,
)
from challenges.utils import (
    add_domain_to_challenge,
    add_prizes_to_challenge,
    add_sponsors_to_challenge,
    add_tags_to_challenge,
    complete_s3_multipart_file_upload,
    generate_presigned_url_for_multipart_upload,
    get_challenge_model,
    get_challenge_phase_model,
    get_challenge_phase_split_model,
    get_dataset_split_model,
    get_leaderboard_model,
    get_participant_model,
    get_unique_alpha_numeric_key,
    is_user_in_allowed_email_domains,
    is_user_in_blocked_email_domains,
    parse_submission_meta_attributes,
)
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from hosts.models import ChallengeHost, ChallengeHostTeam
from hosts.utils import (
    get_challenge_host_team_model,
    get_challenge_host_teams_for_user,
    is_user_a_host_of_challenge,
    is_user_a_staff_or_host,
)
from jobs.filters import SubmissionFilter
from jobs.models import Submission
from jobs.serializers import (
    ChallengeSubmissionManagementSerializer,
    SubmissionSerializer,
)
from jobs.utils import get_submission_model
from participants.models import Participant, ParticipantTeam
from participants.serializers import ParticipantTeamDetailSerializer
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge,
    get_participant_team_of_user_for_a_challenge,
    get_participant_teams_for_user,
    has_user_participated_in_challenge,
    is_user_creator_of_participant_team,
    is_user_part_of_participant_team,
)
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from yaml.scanner import ScannerError

from .aws_utils import (
    create_ec2_instance,
    delete_workers,
    describe_ec2_instance,
    get_log_group_name,
    get_logs_from_cloudwatch,
    restart_ec2_instance,
    restart_workers,
    scale_resources,
    start_ec2_instance,
    start_workers,
    stop_ec2_instance,
    stop_workers,
    terminate_ec2_instance,
)
from .models import (
    Challenge,
    ChallengeConfiguration,
    ChallengeEvaluationCluster,
    ChallengePhase,
    ChallengePhaseSplit,
    ChallengePrize,
    ChallengeSponsor,
    ChallengeTemplate,
    LeaderboardData,
    PWCChallengeLeaderboard,
    StarChallenge,
    UserInvitation,
)
from .permissions import IsChallengeCreator
from .serializers import (
    ChallengeConfigSerializer,
    ChallengeEvaluationClusterSerializer,
    ChallengePhaseCreateSerializer,
    ChallengePhaseSerializer,
    ChallengePhaseSplitSerializer,
    ChallengePrizeSerializer,
    ChallengeSerializer,
    ChallengeSponsorSerializer,
    ChallengeTemplateSerializer,
    DatasetSplitSerializer,
    LeaderboardDataSerializer,
    LeaderboardSerializer,
    PWCChallengeLeaderboardSerializer,
    StarChallengeSerializer,
    UserInvitationSerializer,
    ZipChallengePhaseSplitSerializer,
    ZipChallengeSerializer,
)
from .utils import (
    get_aws_credentials_for_submission,
    get_challenge_template_data,
    get_file_content,
    get_missing_keys_from_dict,
    send_emails,
)

logger = logging.getLogger(__name__)

try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
            if "overview_file" in request.FILES:
                overview_file = request.FILES["overview_file"]
                overview = overview_file.read()
                request.data["description"] = overview
                serializer = ZipChallengeSerializer(
                    challenge,
                    data=request.data,
                    context={
                        "challenge_host_team": challenge_host_team,
                        "request": request,
                    },
                    partial=True,
                )
            elif "terms_and_conditions_file" in request.FILES:
                terms_and_conditions_file = request.FILES[
                    "terms_and_conditions_file"
                ]
                terms_and_conditions = terms_and_conditions_file.read()
                request.data["terms_and_conditions"] = terms_and_conditions
                serializer = ZipChallengeSerializer(
                    challenge,
                    data=request.data,
                    context={
                        "challenge_host_team": challenge_host_team,
                        "request": request,
                    },
                    partial=True,
                )
            elif "submission_guidelines_file" in request.FILES:
                submission_guidelines_file = request.FILES[
                    "submission_guidelines_file"
                ]
                submission_guidelines = submission_guidelines_file.read()
                request.data["submission_guidelines"] = submission_guidelines
                serializer = ZipChallengeSerializer(
                    challenge,
                    data=request.data,
                    context={
                        "challenge_host_team": challenge_host_team,
                        "request": request,
                    },
                    partial=True,
                )
            elif "evaluation_criteria_file" in request.FILES:
                evaluation_criteria_file = request.FILES[
                    "evaluation_criteria_file"
                ]
                evaluation_criteria = evaluation_criteria_file.read()
                request.data["evaluation_details"] = evaluation_criteria
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


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def deregister_participant_team_from_challenge(request, challenge_pk):
    """
    Deregister a participant team from a challenge
    Arguments:
        challenge_pk {int} -- Challenge primary key
    Returns:
        {String} -- Success message
    """
    if has_user_participated_in_challenge(
        user=request.user, challenge_id=challenge_pk
    ):
        challenge = get_challenge_model(challenge_pk)
        participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_pk
        )
        participant_team = get_participant_model(participant_team_pk)
        all_challenge_phases = ChallengePhase.objects.filter(
            challenge=challenge
        )
        if all_challenge_phases.count() > 0:
            for challenge_phase in all_challenge_phases:
                submission_exist = Submission.objects.filter(
                    participant_team=participant_team,
                    challenge_phase=challenge_phase,
                ).exists()
                if submission_exist:
                    break
        else:
            submission_exist = False
        if submission_exist:
            response_data = {
                "error": "Participant teams which have made submissions to a challenge cannot be deregistered."
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )
        else:
            challenge.participant_teams.remove(participant_team)
            response_data = {"success": "Successfully deregistered!"}
            return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "error": "Your participant team is not registered for this challenge."
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def participant_team_detail_for_challenge(request, challenge_pk):
    """
    Returns the participated team detail in the challenge
    Arguments:
        challenge_pk {int} -- Challenge primary key
    Returns:
        {dict} -- Participant team detail that has participated in the challenge
    """
    if has_user_participated_in_challenge(
        user=request.user, challenge_id=challenge_pk
    ):
        challenge = get_challenge_model(challenge_pk)
        participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_pk
        )
        participant_team = get_participant_model(participant_team_pk)
        serializer = ParticipantTeamDetailSerializer(participant_team)
        if challenge.approved_participant_teams.filter(
            pk=participant_team_pk
        ).exists():
            approved = True
        elif not challenge.manual_participant_approval:
            approved = True
        else:
            approved = False
        response_data = {
            "approved": approved,
            "participant_team": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        message = "You are not a participant!"
        response_data = {"error": message}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@extend_schema(
    methods=["GET"],
    operation_id="get_participant_teams_for_challenge",
    parameters=[
        OpenApiParameter(
            name="challenge_pk",
            location=OpenApiParameter.PATH,
            type=int,
            description="Challenge Primary Key (pk)",
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="List of participant teams for the specified challenge"
        ),
        status.HTTP_403_FORBIDDEN: OpenApiResponse(
            description="Unauthorized request",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "You are not authorized to make this request",
                    },
                },
            },
        ),
    },
)
@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_participant_teams_for_challenge(request, challenge_pk):
    """
    API to get all participant team detail

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {[int]} -- Challenge primary key

    Returns:
        {dict} -- Participant team detail that has participated in the challenge
    """

    challenge = get_challenge_model(challenge_pk)
    if is_user_a_host_of_challenge(request.user, challenge_pk):
        participant_teams = challenge.participant_teams
        serializer = ParticipantTeamDetailSerializer(
            participant_teams, many=True
        )
        for participant_team in serializer.data:
            if challenge.approved_participant_teams.filter(
                id=participant_team["id"]
            ).exists():
                participant_team["approved"] = True
            else:
                participant_team["approved"] = False
        response_data = {
            "participant_teams": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "error": "You are not authorized to make this request"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
        domains = ""
        for domain in challenge.allowed_email_domains:
            domains = "{}{}{}".format(domains, "/", domain)
        domains = domains[1:]
        for participant_email in participant_team.get_all_participants_email():
            if not is_user_in_allowed_email_domains(
                participant_email, challenge_pk
            ):
                message = "Sorry, team consisting of users with non-{} email domain(s) are not allowed \
                    to participate in this challenge."
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

    if not (
        is_user_part_of_participant_team(request.user, participant_team)
        or is_user_creator_of_participant_team(request.user, participant_team)
    ):
        response_data = {
            "error": "Sorry, you are not authorized to to make this request"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

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
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def add_participant_team_to_approved_list(
    request, challenge_pk, participant_team_pk
):
    """
    Add participant team to approved list
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "Participant Team does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if challenge.approved_participant_teams.filter(
        pk=participant_team_pk
    ).exists():
        response_data = {"error": "Participant Team already approved"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        if ParticipantTeam.objects.filter(
            team_name__in=challenge.participant_teams.values_list(
                "team_name", flat=True
            )
        ).exists():
            challenge.approved_participant_teams.add(participant_team)
            response_data = {
                "success": "Participant Team added to approved list"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data = {
                "error": "Participant isn't interested in challenge"
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def remove_participant_team_from_approved_list(
    request, challenge_pk, participant_team_pk
):
    """
    Remove participant team from approved list
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
        team_name = participant_team.team_name
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "Participant Team does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    all_challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
    if all_challenge_phases.count() > 0:
        for challenge_phase in all_challenge_phases:
            submission_exist = Submission.objects.filter(
                participant_team=participant_team,
                challenge_phase=challenge_phase,
            ).exists()
            if submission_exist:
                break
    else:
        submission_exist = False
    if (
        challenge.approved_participant_teams.filter(
            pk=participant_team_pk
        ).exists()
        and not submission_exist
    ):
        challenge.approved_participant_teams.remove(participant_team)
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif submission_exist:
        response_data = {
            "error": f"Participant Team {team_name} has existing submissions and cannot be unapproved"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        response_data = {
            "error": f"Participant Team {team_name} was not approved"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator)
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
def get_all_challenges(
    request, challenge_time, challenge_approved, challenge_published
):
    """
    Returns the list of all challenges
    """
    # make sure that a valid url is requested.
    if challenge_time.lower() not in ("all", "future", "past", "present"):
        response_data = {"error": "Wrong url pattern!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if challenge_approved.lower() not in ("all", "approved", "unapproved"):
        response_data = {"error": "Wrong challenge approval status!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if challenge_published.lower() not in ("all", "public", "private"):
        response_data = {"error": "Wrong challenge published status!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    q_params = {}
    if challenge_approved.lower() != "all":
        q_params["approved_by_admin"] = (
            challenge_approved.lower() == "approved"
        )

    if challenge_published.lower() != "all":
        q_params["published"] = challenge_published.lower() == "public"

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
def get_all_challenges_submission_metrics(request):
    """
    Returns the submission metrics for all challenges and their phases
    """
    if not is_user_a_staff(request.user):
        response_data = {
            "error": "Sorry, you are not authorized to make this request"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    challenges = Challenge.objects.all()
    submission_metrics = {}

    submission_statuses = [status[0] for status in Submission.STATUS_OPTIONS]

    for challenge in challenges:
        challenge_id = challenge.id
        challenge_metrics = {}

        # Fetch challenge phases for the challenge
        challenge_phases = ChallengePhase.objects.filter(challenge=challenge)

        for submission_status in submission_statuses:
            count = Submission.objects.filter(
                challenge_phase__in=challenge_phases, status=submission_status
            ).count()
            challenge_metrics[submission_status] = count

        submission_metrics[challenge_id] = challenge_metrics

    return Response(submission_metrics, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def get_challenge_submission_metrics_by_pk(request, pk):
    """
    Returns the submission metrics for a given challenge by primary key and their phases
    """
    if not is_user_a_staff(request.user):
        response_data = {
            "error": "Sorry, you are not authorized to make this request"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    challenge = get_challenge_model(pk)
    challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
    submission_metrics = {}

    submission_statuses = [status[0] for status in Submission.STATUS_OPTIONS]

    # Fetch challenge phases for the challenge
    challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
    for submission_status in submission_statuses:
        count = Submission.objects.filter(
            challenge_phase__in=challenge_phases, status=submission_status
        ).count()
        submission_metrics[submission_status] = count

    return Response(submission_metrics, status=status.HTTP_200_OK)


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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
            if "phase_description_file" in request.FILES:
                phase_description_file = request.FILES[
                    "phase_description_file"
                ]
                phase_description = phase_description_file.read()
                request.data["description"] = phase_description
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
    ).order_by("pk")

    # Check if user is a challenge host or staff
    challenge_host = is_user_a_staff_or_host(request.user, challenge_pk)

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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
            template_zip_s3_url = (
                settings.EVALAI_API_SERVER
                + challenge_template.template_file.url
            )
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
        message = (
            "There are {0} YAML files instead of one in zip folder!".format(
                yaml_file_count
            )
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
            # To capitalize the first alphabet of the problem description as
            # default is in lowercase
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
                    valid_attributes = [
                        "method_name",
                        "method_description",
                        "project_url",
                        "publication_url",
                    ]
                    if not attribute["name"] in valid_attributes:
                        message = "Default meta attribute: {} in phase: {} does not exist!".format(
                            attribute["name"], data["id"]
                        )
                        response_data = {"error": message}
                        return Response(
                            response_data,
                            status=status.HTTP_406_NOT_ACCEPTABLE,
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
                challenge_phase_data[field] = (
                    challenge_phase_data_from_hosts.get(field)
                )
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
                raise RuntimeError()
                # transaction.set_rollback(True)
                # return Response(response_data,
                # status.HTTP_406_NOT_ACCEPTABLE)

            # Add Tags
            add_tags_to_challenge(yaml_file_data, challenge)

            # Add Domain
            verify_complete = add_domain_to_challenge(
                yaml_file_data, challenge
            )
            if verify_complete is not None:
                return Response(
                    verify_complete, status=status.HTTP_400_BAD_REQUEST
                )

            # Add Sponsors
            error_messages = add_sponsors_to_challenge(
                yaml_file_data, challenge
            )
            if error_messages is not None:
                return Response(
                    error_messages, status=status.HTTP_400_BAD_REQUEST
                )

            # Add Prizes
            error_messages = add_prizes_to_challenge(yaml_file_data, challenge)
            if error_messages is not None:
                return Response(
                    error_messages, status=status.HTTP_400_BAD_REQUEST
                )

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
                    raise RuntimeError()

            # Create Challenge Phase
            challenge_phase_ids = {}
            # Delete the challenge phase if it is not present in the yaml file
            existing_challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
            existing_challenge_phase_ids = [str(challenge_phase.config_id) for challenge_phase in existing_challenge_phases]
            challenge_phases_data_ids = [str(challenge_phase_data["id"]) for challenge_phase_data in challenge_phases_data]
            challenge_phase_ids_to_delete = list(set(existing_challenge_phase_ids) - set(challenge_phases_data_ids))
            for challenge_phase_id_to_delete in challenge_phase_ids_to_delete:
                challenge_phase = ChallengePhase.objects.filter(challenge__pk=challenge.pk, config_id=challenge_phase_id_to_delete).first()
                submission_exist = Submission.objects.filter(challenge_phase=challenge_phase).exists()
                if submission_exist:
                    response_data = {
                        "error": "Sorry, you cannot delete a challenge phase with submissions."
                    }
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                else:
                    challenge_phase.delete()

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
                    # This is when the host wants to upload the annotation file
                    # later through CLI
                    serializer = ChallengePhaseCreateSerializer(
                        data=data,
                        context={
                            "challenge": challenge,
                            "config_id": data["id"],
                        },
                    )
                if serializer.is_valid():
                    serializer.save()
                    challenge_phase_ids[str(data["id"])] = (
                        serializer.instance.pk
                    )
                else:
                    response_data = serializer.errors
                    raise RuntimeError()

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
                    raise RuntimeError()

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

            # Delete the challenge phase split if it is not present in the yaml file
            existing_challenge_phase_splits = ChallengePhaseSplit.objects.filter(challenge_phase__challenge=challenge)
            challenge_phase_splits_set = set()
            for challenge_phase_split in existing_challenge_phase_splits:
                challenge_phase = challenge_phase_split.challenge_phase
                dataset_split = challenge_phase_split.dataset_split
                leaderboard = challenge_phase_split.leaderboard
                combination = (challenge_phase, dataset_split, leaderboard)
                challenge_phase_splits_set.add(combination)
            for data in challenge_phase_splits_data:
                challenge_phase = challenge_phase_ids[str(data["challenge_phase_id"])]
                dataset_split = dataset_split_ids[str(data["dataset_split_id"])]
                leaderboard = leaderboard_ids[str(data["leaderboard_id"])]
                combination = (challenge_phase, dataset_split, leaderboard)
                if combination in challenge_phase_splits_set:
                    challenge_phase_splits_set.remove(combination)
            for challenge_phase_split in challenge_phase_splits_set:
                challenge_phase_split_qs = ChallengePhaseSplit.objects.filter(
                    challenge_phase=challenge_phase_split[0],
                    dataset_split=challenge_phase_split[1],
                    leaderboard=challenge_phase_split[2]
                )
                challenge_phase_split_qs.delete()

            for data in challenge_phase_splits_data:
                if (
                    challenge_phase_ids.get(str(data["challenge_phase_id"]))
                    is None
                ):
                    message = "Challenge phase with phase id {} doesn't exist.".format(
                        data["challenge_phase_id"]
                    )
                    response_data = {"error": message}
                    return Response(
                        response_data, status.HTTP_406_NOT_ACCEPTABLE
                    )
                if leaderboard_ids.get(str(data["leaderboard_id"])) is None:
                    message = "Leaderboard with id {} doesn't exist.".format(
                        data["leaderboard_id"]
                    )
                    response_data = {"error": message}
                    return Response(
                        response_data, status.HTTP_406_NOT_ACCEPTABLE
                    )
                leaderboard = leaderboard_ids[str(data["leaderboard_id"])]
                if (
                    dataset_split_ids.get(str(data["dataset_split_id"]))
                    is None
                ):
                    message = "Dataset split with id {} doesn't exist.".format(
                        data["dataset_split_id"]
                    )
                    response_data = {"error": message}
                    return Response(
                        response_data, status.HTTP_406_NOT_ACCEPTABLE
                    )
                challenge_phase = challenge_phase_ids[
                    str(data["challenge_phase_id"])
                ]
                dataset_split = dataset_split_ids[
                    str(data["dataset_split_id"])
                ]
                visibility = data["visibility"]
                leaderboard_decimal_precision = data[
                    "leaderboard_decimal_precision"
                ]
                is_leaderboard_order_descending = data[
                    "is_leaderboard_order_descending"
                ]

                data = {
                    "challenge_phase": challenge_phase,
                    "leaderboard": leaderboard,
                    "dataset_split": dataset_split,
                    "visibility": visibility,
                    "leaderboard_decimal_precision": leaderboard_decimal_precision,
                    "is_leaderboard_order_descending": is_leaderboard_order_descending,
                }

                serializer = ZipChallengePhaseSplitSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    response_data = serializer.errors
                    print(response_data)
                    raise RuntimeError()

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

            if challenge.is_docker_based:
                challenge_evaluation_cluster = ChallengeEvaluationCluster(
                    challenge=zip_config.challenge
                )
                evaluation_cluster_serializer = (
                    ChallengeEvaluationClusterSerializer(
                        challenge_evaluation_cluster,
                        data={
                            "name": "{0}-cluster".format(
                                challenge.title.replace(" ", "-")
                            )
                        },
                        partial=True,
                    )
                )
                if evaluation_cluster_serializer.is_valid():
                    evaluation_cluster_serializer.save()

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
            if (
                not challenge.is_docker_based
                and challenge.inform_hosts
                and not challenge.remote_evaluation
            ):
                try:
                    response = start_workers([zip_config.challenge])
                    count, failures = response["count"], response["failures"]
                    logging.info(
                        "Total worker start count is {} and failures are: {}".format(
                            count, failures
                        )
                    )
                    if count:
                        logging.info(
                            "{} workers started successfully".format(count)
                        )
                        template_id = settings.SENDGRID_SETTINGS.get(
                            "TEMPLATES"
                        ).get("WORKER_START_EMAIL")
                        send_emails(emails, template_id, template_data)
                except Exception:
                    logger.exception(
                        "Failed to start workers for challenge {}".format(
                            zip_config.challenge.pk
                        )
                    )

            response_data = {
                "success": "Challenge {} has been created successfully and"
                " sent for review to EvalAI Admin.".format(challenge.title)
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

    except:  # noqa: E722
        try:
            if response_data:
                response_data = {"error": json.dumps(response_data)}
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


@extend_schema(
    methods=["GET"],
    operation_id="get_all_submissions_for_a_challenge",
    parameters=[
        OpenApiParameter(
            name="challenge_pk",
            location=OpenApiParameter.PATH,
            type=str,
            description="Challenge ID",
            required=True,
        ),
        OpenApiParameter(
            name="challenge_phase_pk",
            location=OpenApiParameter.PATH,
            type=str,
            description="Challenge Phase ID",
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="List of submissions for the challenge phase",
            response={
                "type": "object",
                "properties": {
                    "count": {"type": "string"},
                    "next": {"type": "string"},
                    "previous": {"type": "string"},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "participant_team": {"type": "string"},
                                "challenge_phase": {"type": "string"},
                                "created_by": {"type": "string"},
                                "status": {"type": "string"},
                                "is_public": {"type": "boolean"},
                                "is_flagged": {"type": "boolean"},
                                "submission_number": {"type": "integer"},
                                "submitted_at": {"type": "string"},
                                "execution_time": {"type": "number"},
                                "input_file": {"type": "string"},
                                "stdout_file": {"type": "string"},
                                "stderr_file": {"type": "string"},
                                "environment_log_file": {"type": "string"},
                                "submission_result_file": {"type": "string"},
                                "submission_metadata_file": {"type": "string"},
                                "participant_team_members_email_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "participant_team_members_affiliations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "created_at": {"type": "string"},
                                "method_name": {"type": "string"},
                                "participant_team_members": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Invalid request parameters"
        ),
    },
)
@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_all_submissions_of_challenge(
    request, challenge_pk, challenge_phase_pk
):
    """
    Returns all the submissions for a particular challenge
    """
    # To check for the corresponding challenge from challenge_pk.
    challenge = get_challenge_model(challenge_pk)

    # To check for the corresponding challenge phase from the
    # challenge_phase_pk and challenge.
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

    # To check for the user as a host of the challenge from the request and
    # challenge_pk.
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

    # To check for the user as a participant of the challenge from the request
    # and challenge_pk.
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


@extend_schema(
    methods=["GET"],
    operation_id="download_all_submissions",
    parameters=[
        OpenApiParameter(
            name="challenge_pk",
            location=OpenApiParameter.PATH,
            type=int,
            description="Challenge pk",
            required=True,
        ),
        OpenApiParameter(
            name="challenge_phase_pk",
            location=OpenApiParameter.PATH,
            type=int,
            description="Challenge phase pk",
            required=True,
        ),
        OpenApiParameter(
            name="file_type",
            location=OpenApiParameter.PATH,
            type=str,
            description="File type",
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Submissions successfully downloaded"
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="The file type requested is not valid!"
        ),
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            description="Challenge Phase does not exist"
        ),
    },
)
@extend_schema(
    methods=["POST"],
    operation_id="download_all_submissions",
    parameters=[
        OpenApiParameter(
            name="challenge_pk",
            location=OpenApiParameter.PATH,
            type=int,
            description="Challenge pk",
            required=True,
        ),
        OpenApiParameter(
            name="challenge_phase_pk",
            location=OpenApiParameter.PATH,
            type=int,
            description="Challenge phase pk",
            required=True,
        ),
        OpenApiParameter(
            name="file_type",
            location=OpenApiParameter.PATH,
            type=str,
            description="File type",
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Submissions successfully downloaded",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="The file type requested is not valid!"
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Sorry, you do not belong to this Host Team!"
        ),
    },
)
@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def download_all_submissions(
    request, challenge_pk, challenge_phase_pk, file_type
):
    """
    API endpoint to download all the submissions for a particular challenge as a csv

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {[int]} -- Challenge primary key
        challenge_phase_pk {[int]} -- Challenge phase primary key
        file_type {[str]} -- File type

    Returns:
        Response Object -- An object containing api response
    """
    # To check for the corresponding challenge from challenge_pk.
    challenge = get_challenge_model(challenge_pk)

    # To check for the corresponding challenge phase from the
    # challenge_phase_pk and challenge.
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
                response["Content-Disposition"] = (
                    "attachment; filename=all_submissions.csv"
                )
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
                        "Environment Log File",
                        "Submitted At",
                        "Submission Result File",
                        "Submission Metadata File",
                        "Method Name",
                        "Method Description",
                        "Publication URL",
                        "Project URL",
                        "Submission Meta Attributes",
                    ]
                )
                # Issue: "#" isn't parsed by writer.writerow(), hence it is replaced by "-"
                # TODO: Find a better way to solve the above issue.
                for submission in submissions.data:
                    submission_meta_attributes = (
                        parse_submission_meta_attributes(submission)
                    )
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
                            submission["environment_log_file"],
                            submission["created_at"],
                            submission["submission_result_file"],
                            submission["submission_metadata_file"],
                            submission["method_name"].replace("#", "-"),
                            submission["method_description"].replace("#", "-"),
                            submission["publication_url"],
                            submission["project_url"],
                            submission_meta_attributes,
                        ]
                    )
                return response

            elif has_user_participated_in_challenge(
                user=request.user, challenge_id=challenge_pk
            ):

                # get participant team object for the user for a particular
                # challenge.
                participant_team_pk = (
                    get_participant_team_id_of_user_for_a_challenge(
                        request.user, challenge_pk
                    )
                )

                # Filter submissions on the basis of challenge phase for a
                # participant.
                submissions = Submission.objects.filter(
                    participant_team=participant_team_pk,
                    challenge_phase=challenge_phase,
                ).order_by("-submitted_at")
                submissions = ChallengeSubmissionManagementSerializer(
                    submissions, many=True, context={"request": request}
                )
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    "attachment; filename=all_submissions.csv"
                )
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
                    "environment_log_file": "Environment Log File",
                    "created_at": "Submitted At (mm/dd/yyyy hh:mm:ss)",
                    "submission_result_file": "Submission Result File",
                    "submission_metadata_file": "Submission Metadata File",
                    "method_name": "Method Name",
                    "method_description": "Method Description",
                    "publication_url": "Publication URL",
                    "project_url": "Project URL",
                    "submission_meta_attributes": "Submission Meta Attributes",
                }
                submissions = Submission.objects.filter(
                    challenge_phase__challenge=challenge
                ).order_by("-submitted_at")
                submissions = ChallengeSubmissionManagementSerializer(
                    submissions, many=True, context={"request": request}
                )
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    "attachment; filename=all_submissions.csv"
                )
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
                        elif field == "submission_meta_attributes":
                            submission_meta_attributes = (
                                parse_submission_meta_attributes(submission)
                            )
                            row.append(submission_meta_attributes)
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_or_update_leaderboard(request, leaderboard_pk):
    """
    Returns or Updates a leaderboard
    """
    leaderboard = get_leaderboard_model(leaderboard_pk)

    if request.method == "PATCH":
        if "schema" in request.data.keys():
            request.data["schema"] = json.loads(request.data["schema"])
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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


@api_view(["PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_challenge_tags_and_domain(request, challenge_pk):
    """
    Returns or Updates challenge tags and domain
    """
    challenge = get_challenge_model(challenge_pk)

    if request.method == "PATCH":
        new_tags = request.data.get("list_tags", [])
        domain_value = request.data.get("domain")
        # Remove tags not present in the YAML file
        challenge.list_tags = [
            tag for tag in challenge.list_tags if tag in new_tags
        ]
        # Add new tags to the challenge
        for tag_name in new_tags:
            if tag_name not in challenge.list_tags:
                challenge.list_tags.append(tag_name)
        # Verifying Domain name
        valid_domains = [choice[0] for choice in challenge.DOMAIN_OPTIONS]
        if domain_value in valid_domains:
            challenge.domain = domain_value
            challenge.save()
            return Response(status=status.HTTP_200_OK)
        else:
            message = f"Invalid domain value:{domain_value}"
            response_data = {"error": message}
            return Response(response_data, status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_domain_choices(request):
    """
    Returns domain choices
    """
    if request.method == "GET":
        domain_choices = Challenge.DOMAIN_OPTIONS
        return Response(domain_choices, status.HTTP_200_OK)
    else:
        response_data = {"error": "Method not allowed"}
        return Response(response_data, status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
def get_prizes_by_challenge(request, challenge_pk):
    """
    Returns a list of prizes for a given challenge.
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    prizes = ChallengePrize.objects.filter(challenge=challenge)
    serializer = ChallengePrizeSerializer(prizes, many=True)
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
def get_sponsors_by_challenge(request, challenge_pk):
    """
    Returns a list of sponsors for a given challenge.
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    sponsors = ChallengeSponsor.objects.filter(challenge=challenge)
    serializer = ChallengeSponsorSerializer(sponsors, many=True)
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def validate_challenge_config(request, challenge_host_team_pk):
    challenge_host_team = get_challenge_host_team_model(challenge_host_team_pk)

    response_data = {}

    BASE_LOCATION = tempfile.mkdtemp()
    unique_folder_name = get_unique_alpha_numeric_key(10)
    CHALLENGE_ZIP_DOWNLOAD_LOCATION = join(
        BASE_LOCATION, "{}.zip".format(unique_folder_name)
    )

    challenge_queryset = Challenge.objects.filter(
        github_repository=request.data["GITHUB_REPOSITORY"]
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

    error_messages, _yaml_file_data, _files = validate_challenge_config_util(
        request,
        challenge_host_team,
        BASE_LOCATION,
        unique_folder_name,
        zip_ref,
        challenge_queryset[0] if challenge_queryset else None,
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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_worker_logs(request, challenge_pk):
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized to access the worker logs."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)
    response_data = []

    log_group_name = get_log_group_name(challenge.pk)
    log_stream_prefix = challenge.queue
    pattern = ""  # Empty string to get all logs including container logs.

    # This is to specify the time window for fetching logs: 3 days before from
    # current time.
    timeframe = 4320
    limit = 1000
    current_time = int(round(time.time() * 1000))
    start_time = current_time - (timeframe * 60000)
    end_time = current_time

    logs = get_logs_from_cloudwatch(
        log_group_name, log_stream_prefix, start_time, end_time, pattern, limit
    )

    response_data = {"logs": logs}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def scale_resources_by_challenge_pk(request, challenge_pk):
    """
    The function called by a host to update the resources used by their challenge.

    Calls the scale_resources method. Before calling, checks if the caller hosts the challenge and provided valid CPU
    unit counts and memory sizes (MB).

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {int} -- The challenge pk for which its workers' resources will be updated

    Returns:
        Response object -- Response object with appropriate response code (200/400/403/404)
    """
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized for access worker operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("worker_cpu_cores") is None:
        response_data = {"error": "vCPU config missing from request data."}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("worker_memory") is None:
        response_data = {
            "error": "Worker memory config missing from request data."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)
    if challenge.workers is None or challenge.workers == 0:
        response_data = {"error": "Scaling inactive workers not supported."}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    worker_cpu_cores = int(request.data["worker_cpu_cores"])
    worker_memory = int(request.data["worker_memory"])

    if (
        worker_cpu_cores == 256
        and worker_memory in (512, 1024, 2048)
        or worker_cpu_cores == 512
        and worker_memory in (1024, 2048)
        or worker_cpu_cores == 1024
        and worker_memory == 2048
    ):
        response = scale_resources(challenge, worker_cpu_cores, worker_memory)
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            if (
                response.get(
                    "Error", {"Message": "No error", "Code": "No error"}
                ).get("Code", "No error code")
                == "ClientException"
            ):
                response_data = {
                    "error": "Challenge workers are inactive or do not exist."
                }
            else:
                response_data = {"error": "Issue with ECS."}
            return Response(
                response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        elif response.get("Message", "N/A") == "Worker not modified":
            response_data = {
                "Success": "The challenge's worker cores and memory were not modified."
            }
        else:
            response_data = {"Success": "Worker scaled successfully!"}
    else:
        response_data = {
            "error": "Please specify correct config for worker vCPU and memory."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def manage_worker(request, challenge_pk, action):
    if not request.user.is_staff:
        if not is_user_a_host_of_challenge(request.user, challenge_pk):
            response_data = {
                "error": "Sorry, you are not authorized for access worker operations."
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # make sure that the action is valid.
    if action not in ("start", "stop", "restart", "delete"):
        response_data = {
            "error": "The action {} is invalid for worker".format(action)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Only allow EvalAI admins to delete workers
    if action == "delete" and not request.user.is_staff:
        response_data = {
            "error": "Sorry, you are not authorized for access worker operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)

    if challenge.end_date < pytz.UTC.localize(
        datetime.utcnow()
    ) and action in ("start", "stop", "restart"):
        response_data = {
            "error": "Action {} worker is not supported for an inactive challenge.".format(
                action
            )
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    response_data = {}

    if action == "start":
        response = start_workers([challenge])
    elif action == "stop":
        response = stop_workers([challenge])
    elif action == "restart":
        response = restart_workers([challenge])
    elif action == "delete":
        response = delete_workers([challenge])

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
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_ec2_instance_details(request, challenge_pk):
    if not request.user.is_staff:
        response_data = {
            "error": "Sorry, you are not authorized for access EC2 operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)

    if not challenge.uses_ec2_worker:
        response_data = {
            "error": "Challenge does not use EC2 worker instance."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    response = describe_ec2_instance(challenge)
    if response:
        if "error" not in response:
            status_code = status.HTTP_200_OK
            response_data = {
                "message": response["message"],
                "action": "Success",
            }
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response_data = {
                "message": response["error"],
                "action": "Failure",
            }
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = {
            "message": "No Response",
            "action": "Failure",
        }
    return Response(response_data, status=status_code)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def delete_ec2_instance_by_challenge_pk(request, challenge_pk):
    if not request.user.is_staff:
        response_data = {
            "error": "Sorry, you are not authorized for access EC2 operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)

    if not challenge.ec2_instance_id:
        response_data = {
            "error": "No EC2 instance ID found for the challenge. Please ensure instance ID exists."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    response = terminate_ec2_instance(challenge)

    if response:
        if "error" not in response:
            status_code = status.HTTP_200_OK
            response_data = {
                "message": response["message"],
                "action": "Success",
            }
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response_data = {
                "message": response["error"],
                "action": "Failure",
            }
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = {
            "message": "No Response",
            "action": "Failure",
        }
    return Response(response_data, status=status_code)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def create_ec2_instance_by_challenge_pk(request, challenge_pk):
    """
    API to create EC2 instance for a challenge
    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {int} -- The challenge pk for which the EC2 instance is to be created
    Query Parameters:
        ec2_storage -- Storage size for EC2 instance
        worker_instance_type -- Instance type for EC2 instance
        worker_image_url -- Image URL for EC2 instance
    Returns:
        Response object -- Response object with appropriate response code (200/400/403/404)
    """
    if request.method == "PUT":
        ec2_storage = request.data.get("ec2_storage", None)
        worker_instance_type = request.data.get("worker_instance_type", None)
        worker_image_url = request.data.get("worker_image_url", None)
    if not request.user.is_staff:
        response_data = {
            "error": "Sorry, you are not authorized for access EC2 operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = get_challenge_model(challenge_pk)

    if challenge.end_date < pytz.UTC.localize(datetime.utcnow()):
        response_data = {
            "error": "Creation of EC2 instance is not supported for an inactive challenge."
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if ec2_storage and not isinstance(ec2_storage, int):
        response_data = {
            "error": "Passed value of EC2 storage should be integer."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if worker_instance_type and not isinstance(worker_instance_type, str):
        response_data = {
            "error": "Passed value of worker instance type should be string."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if worker_image_url and not isinstance(worker_image_url, str):
        response_data = {
            "error": "Passed value of worker image URL should be string."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not ec2_storage:
        ec2_storage = challenge.ec2_storage

    if not worker_instance_type:
        worker_instance_type = challenge.worker_instance_type

    if not worker_image_url:
        worker_image_url = challenge.worker_image_url

    response = create_ec2_instance(
        challenge, ec2_storage, worker_instance_type, worker_image_url
    )

    if response:
        if "error" not in response:
            status_code = status.HTTP_200_OK
            response_data = {
                "message": response["message"],
                "action": "Success",
            }
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response_data = {
                "message": response["error"],
                "action": "Failure",
            }
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = {
            "message": "No Response",
            "action": "Failure",
        }
    return Response(response_data, status=status_code)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def manage_ec2_instance(request, challenge_pk, action):
    if not request.user.is_staff:
        response_data = {
            "error": "Sorry, you are not authorized for access EC2 operations."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # make sure that the action is valid.
    if action not in ("start", "stop", "restart"):
        response_data = {
            "error": "The action {} is invalid for worker".format(action)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge = get_challenge_model(challenge_pk)

    if not challenge.uses_ec2_worker:
        response_data = {
            "error": "Challenge does not use EC2 worker instance."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if challenge.end_date < pytz.UTC.localize(
        datetime.utcnow()
    ) and action in ("start", "restart"):
        response_data = {
            "error": "Action {} EC2 instance is not supported for an inactive challenge.".format(
                action
            )
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if action == "start":
        response = start_ec2_instance(challenge)
    elif action == "stop":
        response = stop_ec2_instance(challenge)
    elif action == "restart":
        response = restart_ec2_instance(challenge)

    if response:
        if "error" not in response:
            status_code = status.HTTP_200_OK
            response_data = {
                "message": response["message"],
                "action": "Success",
            }
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response_data = {
                "message": response["error"],
                "action": "Failure",
            }
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = {
            "message": "No Response",
            "action": "Failure",
        }
    return Response(response_data, status=status_code)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_annotation_file_presigned_url(request, challenge_phase_pk):
    """
    API to generate a presigned url to upload a test annotation file

    Arguments:
        request {HttpRequest} -- The request object
        challenge_phase_pk {int} -- Challenge phase primary key
    Returns:
         Response Object -- An object containing the presignd url, or an error message if some failure occurs
    """
    if settings.DEBUG:
        response_data = {
            "error": "Sorry, this feature is not available in development or test environment."
        }
        return Response(response_data)
    # Check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    if not is_user_a_host_of_challenge(
        request.user, challenge_phase.challenge.pk
    ):
        response_data = {
            "error": "Sorry, you are not authorized for uploading an annotation file."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Set default num of chunks to 1 if num of chunks is not specified
    num_file_chunks = 1
    if request.data.get("num_file_chunks"):
        num_file_chunks = int(request.data["num_file_chunks"])

    file_ext = os.path.splitext(request.data["file_name"])[-1]
    random_file_name = uuid.uuid4()

    if challenge_phase.test_annotation:
        file_key_on_s3 = "{}/{}".format(
            settings.MEDIAFILES_LOCATION, challenge_phase.test_annotation.name
        )
    else:
        # This file shall be replaced with the one uploaded through the
        # presigned url from the CLI
        test_annotation_file = SimpleUploadedFile(
            "{}{}".format(random_file_name, file_ext),
            b"Dummy file content",
            content_type="text/plain",
        )
        serializer = ChallengePhaseCreateSerializer(
            challenge_phase,
            data={"test_annotation": test_annotation_file},
            context={
                "challenge": challenge_phase.challenge,
            },
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

    response = generate_presigned_url_for_multipart_upload(
        file_key_on_s3, challenge_phase.challenge.pk, num_file_chunks
    )
    if response.get("error"):
        response_data = response
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    response_data = {
        "presigned_urls": response.get("presigned_urls"),
        "upload_id": response.get("upload_id"),
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def finish_annotation_file_upload(request, challenge_phase_pk):
    """
    API to complete multipart upload for a test annotation file

    Arguments:
        request {HttpRequest} -- The request object
        challenge_phase_pk {int} -- Challenge phase primary key
    Returns:
         Response Object -- An object containing the presignd url, or an error message if some failure occurs
    """
    if settings.DEBUG:
        response_data = {
            "error": "Sorry, this feature is not available in development or test environment."
        }
        return Response(response_data)
    # Check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    if not is_user_a_host_of_challenge(
        request.user, challenge_phase.challenge.pk
    ):
        response_data = {
            "error": "Sorry, you are not authorized for uploading an annotation file."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("parts") is None:
        response_data = {"error": "Uploaded file parts metadata is missing!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("upload_id") is None:
        response_data = {"error": "Uploaded file upload Id is missing!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    file_parts = json.loads(request.data["parts"])
    upload_id = request.data["upload_id"]
    file_key_on_s3 = "{}/{}".format(
        settings.MEDIAFILES_LOCATION, challenge_phase.test_annotation.name
    )
    annotations_uploaded_using_cli = request.data.get(
        "annotations_uploaded_using_cli"
    )
    response = {}
    try:
        data = complete_s3_multipart_file_upload(
            file_parts, upload_id, file_key_on_s3, challenge_phase.challenge.pk
        )
        if data.get("error"):
            response_data = data
            response = Response(
                response_data, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            response_data = {
                "upload_id": upload_id,
                "challenge_phase_pk": challenge_phase.pk,
            }
            response = Response(response_data, status=status.HTTP_201_CREATED)

            if annotations_uploaded_using_cli:
                serializer = ChallengePhaseCreateSerializer(
                    challenge_phase,
                    data={"annotations_uploaded_using_cli": True},
                    context={
                        "challenge": challenge_phase.challenge,
                    },
                    partial=True,
                )
                if serializer.is_valid():
                    serializer.save()
                else:
                    response_data = {"error": serializer.errors}
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )
    except Exception:
        response_data = {
            "error": "Error occurred while uploading annotations!"
        }
        response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    return response


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def create_or_update_github_challenge(request, challenge_host_team_pk):
    try:
        challenge_host_team = get_challenge_host_team_model(
            challenge_host_team_pk
        )
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
        challenge_queryset[0] if challenge_queryset else None,
    )

    if not len(error_messages):
        if not challenge_queryset:
            error_messages = None
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

                    # Add Tags
                    add_tags_to_challenge(yaml_file_data, challenge)

                    # Add Domain
                    verify_complete = add_domain_to_challenge(
                        yaml_file_data, challenge
                    )
                    if verify_complete is not None:
                        return Response(
                            verify_complete, status=status.HTTP_400_BAD_REQUEST
                        )

                    # Add Sponsors
                    error_messages = add_sponsors_to_challenge(
                        yaml_file_data, challenge
                    )
                    if error_messages is not None:
                        return Response(
                            error_messages, status=status.HTTP_400_BAD_REQUEST
                        )

                    # Add Prizes
                    error_messages = add_prizes_to_challenge(
                        yaml_file_data, challenge
                    )
                    if error_messages is not None:
                        return Response(
                            error_messages, status=status.HTTP_400_BAD_REQUEST
                        )

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
                        else:
                            error_messages = f"leaderboard {data['id']} :{str(serializer.errors)}"
                            raise RuntimeError()
                        leaderboard_ids[str(data["id"])] = (
                            serializer.instance.pk
                        )

                    # Create Challenge Phase
                    challenge_phase_ids = {}
                    challenge_phases_data = yaml_file_data["challenge_phases"]

                    # Delete the challenge phase if it is not present in the yaml file
                    existing_challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
                    existing_challenge_phase_ids = [str(challenge_phase.config_id) for challenge_phase in existing_challenge_phases]
                    challenge_phases_data_ids = [str(challenge_phase_data["id"]) for challenge_phase_data in challenge_phases_data]
                    challenge_phase_ids_to_delete = list(set(existing_challenge_phase_ids) - set(challenge_phases_data_ids))
                    for challenge_phase_id_to_delete in challenge_phase_ids_to_delete:
                        challenge_phase = ChallengePhase.objects.filter(
                            challenge__pk=challenge.pk, config_id=challenge_phase_id_to_delete
                        ).first()
                        submission_exist = Submission.objects.filter(challenge_phase=challenge_phase).exists()
                        if submission_exist:
                            response_data = {
                                "error": "Sorry, you cannot delete a challenge phase with submissions."
                            }
                            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            challenge_phase.delete()

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
                            # This is when the host wants to upload the
                            # annotation file later
                            serializer = ChallengePhaseCreateSerializer(
                                data=data,
                                context={
                                    "challenge": challenge,
                                    "config_id": data["id"],
                                },
                            )
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            error_messages = f"challenge phase {data['id']} :{str(serializer.errors)}"
                            raise RuntimeError()
                        challenge_phase_ids[str(data["id"])] = (
                            serializer.instance.pk
                        )

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
                        else:
                            error_messages = f"dataset split {data['id']} :{str(serializer.errors)}"
                            raise RuntimeError()
                        dataset_split_ids[str(data["id"])] = (
                            serializer.instance.pk
                        )

                    # Create Challenge Phase Splits
                    challenge_phase_splits_data = yaml_file_data[
                        "challenge_phase_splits"
                    ]
                    for data in challenge_phase_splits_data:
                        if (
                            challenge_phase_ids.get(
                                str(data["challenge_phase_id"])
                            )
                            is None
                        ):
                            message = "Challenge phase with phase id {} doesn't exist.".format(
                                data["challenge_phase_id"]
                            )
                            response_data = {"error": message}
                            return Response(
                                response_data, status.HTTP_406_NOT_ACCEPTABLE
                            )
                        if (
                            leaderboard_ids.get(str(data["leaderboard_id"]))
                            is None
                        ):
                            message = (
                                "Leaderboard with id {} doesn't exist.".format(
                                    data["leaderboard_id"]
                                )
                            )
                            response_data = {"error": message}
                            return Response(
                                response_data, status.HTTP_406_NOT_ACCEPTABLE
                            )
                        if (
                            dataset_split_ids.get(
                                str(data["dataset_split_id"])
                            )
                            is None
                        ):
                            message = "Dataset split with id {} doesn't exist.".format(
                                data["dataset_split_id"]
                            )
                            response_data = {"error": message}
                            return Response(
                                response_data, status.HTTP_406_NOT_ACCEPTABLE
                            )
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
                        leaderboard_decimal_precision = data[
                            "leaderboard_decimal_precision"
                        ]
                        is_leaderboard_order_descending = data[
                            "is_leaderboard_order_descending"
                        ]

                        data = {
                            "challenge_phase": challenge_phase,
                            "leaderboard": leaderboard,
                            "dataset_split": dataset_split,
                            "visibility": visibility,
                            "is_leaderboard_order_descending": is_leaderboard_order_descending,
                            "leaderboard_decimal_precision": leaderboard_decimal_precision,
                        }

                        serializer = ZipChallengePhaseSplitSerializer(
                            data=data
                        )
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            error_messages = f"challenge phase split (phase:{data['challenge_phase_id']}, leaderboard:{data['leaderboard_id']}, dataset split: {data['dataset_split_id']}):{str(serializer.errors)}"
                            raise RuntimeError()

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
                    "error": f"Error in creating challenge: {error_messages}. Please check the yaml configuration!"
                }
                if error_messages:
                    response_data["error_message"] = json.dumps(error_messages)
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
            try:
                error_messages = None
                # Updating ChallengeConfiguration object
                challenge_configuration = (
                    ChallengeConfiguration.objects.filter(
                        challenge=challenge.pk
                    ).first()
                )
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
                else:
                    error_messages = f"challenge :{str(serializer.errors)}"
                    raise RuntimeError()
                challenge = serializer.instance

                # Add Tags
                add_tags_to_challenge(yaml_file_data, challenge)

                # Add Domain
                verify_complete = add_domain_to_challenge(
                    yaml_file_data, challenge
                )
                if verify_complete is not None:
                    return Response(
                        verify_complete, status=status.HTTP_400_BAD_REQUEST
                    )

                # Add/Update Sponsors
                error_messages = add_sponsors_to_challenge(
                    yaml_file_data, challenge
                )
                if error_messages is not None:
                    return Response(
                        error_messages, status=status.HTTP_400_BAD_REQUEST
                    )

                # Add/Update Prizes
                error_messages = add_prizes_to_challenge(
                    yaml_file_data, challenge
                )
                if error_messages is not None:
                    return Response(
                        error_messages, status=status.HTTP_400_BAD_REQUEST
                    )

                # Updating Leaderboard object
                leaderboard_ids = {}
                yaml_file_data_of_leaderboard = yaml_file_data["leaderboard"]
                for data in yaml_file_data_of_leaderboard:
                    challenge_phase_split_qs = (
                        ChallengePhaseSplit.objects.filter(
                            challenge_phase__challenge__pk=challenge.pk,
                            leaderboard__config_id=data["config_id"],
                        )
                    )
                    if challenge_phase_split_qs:
                        challenge_phase_split = (
                            challenge_phase_split_qs.first()
                        )
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
                        leaderboard_ids[str(data["id"])] = (
                            serializer.instance.pk
                        )
                    else:
                        error_messages = f"leaderboard update {(data['id'])} :{str(serializer.errors)}"
                        raise RuntimeError()

                # Updating ChallengePhase objects
                challenge_phase_ids = {}
                challenge_phases_data = yaml_file_data["challenge_phases"]
                for data, challenge_test_annotation_file in zip(
                    challenge_phases_data,
                    files["challenge_test_annotation_files"],
                ):

                    # Override the submission_meta_attributes when they are
                    # missing
                    submission_meta_attributes = data.get(
                        "submission_meta_attributes"
                    )
                    if submission_meta_attributes is None:
                        data["submission_meta_attributes"] = None

                    # Override the default_submission_meta_attributes when they
                    # are missing
                    default_submission_meta_attributes = data.get(
                        "default_submission_meta_attributes"
                    )
                    if default_submission_meta_attributes is None:
                        data["default_submission_meta_attributes"] = None

                    challenge_phase = ChallengePhase.objects.filter(
                        challenge__pk=challenge.pk, config_id=data["id"]
                    ).first()
                    if (
                        challenge_test_annotation_file
                    ):
                        serializer = ChallengePhaseCreateSerializer(
                            challenge_phase,
                            data=data,
                            context={
                                "challenge": challenge,
                                "test_annotation": challenge_test_annotation_file,
                                "config_id": data["config_id"],
                            },
                        )
                    elif (
                        challenge_test_annotation_file
                        and challenge_phase.annotations_uploaded_using_cli
                    ):
                        data.pop("test_annotation", None)
                        serializer = ChallengePhaseCreateSerializer(
                            challenge_phase,
                            data=data,
                            context={
                                "challenge": challenge,
                                "config_id": data["config_id"],
                            },
                            partial=True,
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
                        challenge_phase_ids[str(data["id"])] = (
                            serializer.instance.pk
                        )
                    else:
                        error_messages = f"challenge phase update {(data['id'])} :{str(serializer.errors)}"
                        raise RuntimeError()

                # Updating DatasetSplit objects
                yaml_file_data_of_dataset_split = yaml_file_data[
                    "dataset_splits"
                ]
                dataset_split_ids = {}
                for data in yaml_file_data_of_dataset_split:
                    challenge_phase_split_qs = (
                        ChallengePhaseSplit.objects.filter(
                            challenge_phase__challenge__pk=challenge.pk,
                            dataset_split__config_id=data["id"],
                        )
                    )
                    if challenge_phase_split_qs:
                        challenge_phase_split = (
                            challenge_phase_split_qs.first()
                        )
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
                        dataset_split_ids[str(data["id"])] = (
                            serializer.instance.pk
                        )
                    else:
                        error_messages = f"dataset split update {(data['id'])} :{str(serializer.errors)}"
                        raise RuntimeError()

                # Update ChallengePhaseSplit objects
                challenge_phase_splits_data = yaml_file_data[
                    "challenge_phase_splits"
                ]

                # Delete the challenge phase split if it is not present in the yaml file
                existing_challenge_phase_splits = ChallengePhaseSplit.objects.filter(challenge_phase__challenge=challenge)
                challenge_phase_splits_set = set()
                for challenge_phase_split in existing_challenge_phase_splits:
                    challenge_phase = challenge_phase_split.challenge_phase
                    dataset_split = challenge_phase_split.dataset_split
                    leaderboard = challenge_phase_split.leaderboard
                    combination = (challenge_phase, dataset_split, leaderboard)
                    challenge_phase_splits_set.add(combination)
                for data in challenge_phase_splits_data:
                    challenge_phase = challenge_phase_ids[str(data["challenge_phase_id"])]
                    dataset_split = dataset_split_ids[str(data["dataset_split_id"])]
                    leaderboard = leaderboard_ids[str(data["leaderboard_id"])]
                    combination = (challenge_phase, dataset_split, leaderboard)
                    if combination in challenge_phase_splits_set:
                        challenge_phase_splits_set.remove(combination)
                for challenge_phase_split in challenge_phase_splits_set:
                    challenge_phase_split_qs = ChallengePhaseSplit.objects.filter(
                        challenge_phase=challenge_phase_split[0],
                        dataset_split=challenge_phase_split[1],
                        leaderboard=challenge_phase_split[2]
                    )
                    challenge_phase_split_qs.delete()

                for data in challenge_phase_splits_data:
                    if (
                        challenge_phase_ids.get(
                            str(data["challenge_phase_id"])
                        )
                        is None
                    ):
                        message = "Challenge phase with phase id {} doesn't exist.".format(
                            data["challenge_phase_id"]
                        )
                        response_data = {"error": message}
                        return Response(
                            response_data, status.HTTP_406_NOT_ACCEPTABLE
                        )
                    if (
                        leaderboard_ids.get(str(data["leaderboard_id"]))
                        is None
                    ):
                        message = (
                            "Leaderboard with id {} doesn't exist.".format(
                                data["leaderboard_id"]
                            )
                        )
                        response_data = {"error": message}
                        return Response(
                            response_data, status.HTTP_406_NOT_ACCEPTABLE
                        )
                    if (
                        dataset_split_ids.get(str(data["dataset_split_id"]))
                        is None
                    ):
                        message = (
                            "Dataset split with id {} doesn't exist.".format(
                                data["dataset_split_id"]
                            )
                        )
                        response_data = {"error": message}
                        return Response(
                            response_data, status.HTTP_406_NOT_ACCEPTABLE
                        )
                    challenge_phase = challenge_phase_ids[
                        str(data["challenge_phase_id"])
                    ]
                    leaderboard = leaderboard_ids[str(data["leaderboard_id"])]
                    dataset_split = dataset_split_ids[
                        str(data["dataset_split_id"])
                    ]
                    visibility = data["visibility"]
                    leaderboard_decimal_precision = data[
                        "leaderboard_decimal_precision"
                    ]
                    is_leaderboard_order_descending = data[
                        "is_leaderboard_order_descending"
                    ]

                    data = {
                        "challenge_phase": challenge_phase,
                        "leaderboard": leaderboard,
                        "dataset_split": dataset_split,
                        "visibility": visibility,
                        "is_leaderboard_order_descending": is_leaderboard_order_descending,
                        "leaderboard_decimal_precision": leaderboard_decimal_precision,
                    }

                    challenge_phase_split_qs = (
                        ChallengePhaseSplit.objects.filter(
                            challenge_phase__pk=challenge_phase,
                            dataset_split__pk=dataset_split,
                            leaderboard__pk=leaderboard,
                        )
                    )
                    if challenge_phase_split_qs:
                        challenge_phase_split = (
                            challenge_phase_split_qs.first()
                        )
                        serializer = ZipChallengePhaseSplitSerializer(
                            challenge_phase_split, data=data
                        )
                    else:
                        serializer = ZipChallengePhaseSplitSerializer(
                            data=data
                        )
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        error_messages = f"challenge phase split update (phase:{data['challenge_phase_id']}, leaderboard:{data['leaderboard_id']}, dataset split: {data['dataset_split_id']}):{str(serializer.errors)}"
                        raise RuntimeError()

                response_data = {
                    "Success": "The challenge {} has been updated successfully".format(
                        challenge.title
                    )
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except:  # noqa: E722
                response_data = {
                    "error": f"Error in creating challenge: {error_messages}. Please check the yaml configuration!"
                }
                if error_messages:
                    response_data["error_message"] = json.dumps(error_messages)
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )
    else:
        shutil.rmtree(BASE_LOCATION)
        logger.info("Challenge config validation failed. Zip folder removed")
        response_data["error"] = "\n".join(error_messages)
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_all_challenge_templates(request):
    q_params = {"is_active": True}
    challenges = ChallengeTemplate.objects.filter(**q_params).order_by("-pk")
    serializer = ChallengeTemplateSerializer(
        challenges, many=True, context={"request": request}
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def pwc_task_dataset(request):
    if request.user.is_staff:
        challenge_mapping = PWCChallengeLeaderboard.objects.filter(
            enable_sync=True
        )
        serializer = PWCChallengeLeaderboardSerializer(
            challenge_mapping, many=True, context={"request": request}
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "error": "You are not authorized to make this request. Please ask EvalAI admin to add you as a staff user for accessing this API."
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@extend_schema(
    methods=["GET"],
    operation_id="get_allowed_email_ids",
    parameters=[
        OpenApiParameter(
            name="challenge_pk",
            location=OpenApiParameter.PATH,
            type=str,
            description="Challenge ID",
            required=True,
        ),
        OpenApiParameter(
            name="phase_pk",
            location=OpenApiParameter.PATH,
            type=str,
            description="Challenge Phase ID",
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="List of allowed email IDs for the challenge phase",
            response={
                "type": "object",
                "properties": {
                    "allowed_email_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of allowed email IDs",
                    }
                },
            },
        ),
    },
)
@extend_schema(
    methods=["DELETE", "PATCH"],
    operation_id="update_allowed_email_ids",
    parameters=[
        OpenApiParameter(
            name="challenge_pk",
            location=OpenApiParameter.PATH,
            type=str,
            description="Challenge ID",
            required=True,
        ),
        OpenApiParameter(
            name="phase_pk",
            location=OpenApiParameter.PATH,
            type=str,
            description="Challenge Phase ID",
            required=True,
        ),
    ],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "allowed_email_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of allowed email ids",
                }
            },
            "required": ["allowed_email_ids"],
        }
    },
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Successfully updated allowed email ids",
            response={
                "type": "object",
                "properties": {
                    "allowed_email_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of allowed email ids",
                    }
                },
            },
        ),
    },
)
@api_view(["GET", "PATCH", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes(
    (
        permissions.IsAuthenticated,
        HasVerifiedEmail,
        IsChallengeCreator,
    )
)
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_allowed_email_ids(request, challenge_pk, phase_pk):
    """
    API to GET/UPDATE/DELETE email ids from challenge phase allowed email ids
    Arguments:
        challenge_pk {int} -- Challenge primary key
        phase_pk {int} -- Challenge phase primary key
    Returns:
        {dict} -- Response object
    """
    challenge = get_challenge_model(challenge_pk)

    try:
        challenge_phase = ChallengePhase.objects.get(
            challenge=challenge, pk=phase_pk
        )
    except ChallengePhase.DoesNotExist:
        response_data = {
            "error": "Challenge phase {} does not exist for challenge {}".format(
                phase_pk, challenge.pk
            )
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    allowed_email_ids = challenge_phase.allowed_email_ids

    if allowed_email_ids is None:
        allowed_email_ids = []

    if request.method != "GET":
        if request.data.get("allowed_email_ids") is not None:
            if not isinstance(request.data["allowed_email_ids"], list):
                response_data = {
                    "error": "Field allowed_email_ids should be a list."
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            response_data = {"error": "Field allowed_email_ids is missing."}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        serializer = ChallengePhaseCreateSerializer(
            challenge_phase, context={"request": request}
        )
        response_data = {
            "allowed_email_ids": serializer.data["allowed_email_ids"],
        }
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ["PATCH"]:
        allowed_email_ids.extend(request.data["allowed_email_ids"])
        allowed_email_ids = list(set(allowed_email_ids))
        serializer = ChallengePhaseCreateSerializer(
            challenge_phase,
            data={"allowed_email_ids": allowed_email_ids},
            context={"challenge": challenge},
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            challenge_phase = get_challenge_phase_model(serializer.instance.pk)
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = response_data = {
                "allowed_email_ids": serializer.data["allowed_email_ids"],
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    elif request.method == "DELETE":
        remove_allowed_email_ids = request.data["allowed_email_ids"]
        allowed_email_ids = list(
            set(allowed_email_ids).difference(set(remove_allowed_email_ids))
        )

        serializer = ChallengePhaseCreateSerializer(
            challenge_phase,
            data={"allowed_email_ids": allowed_email_ids},
            context={"challenge": challenge},
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            challenge_phase = get_challenge_phase_model(serializer.instance.pk)
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = response_data = {
                "allowed_email_ids": serializer.data["allowed_email_ids"],
            }
            return Response(response_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def request_challenge_approval_by_pk(request, challenge_pk):
    """
    Checks if all challenge phases have finished submissions for the given challenge
    and send approval request for the challenge
    """
    challenge = get_challenge_model(challenge_pk)
    challenge_phases = ChallengePhase.objects.filter(challenge=challenge)
    unfinished_phases = []

    for challenge_phase in challenge_phases:
        submissions = Submission.objects.filter(
            challenge_phase=challenge_phase, status="finished"
        )

        if not submissions.exists():
            unfinished_phases.append(challenge_phase.name)

    if unfinished_phases:
        error_message = f"The following challenge phases do not have finished submissions: {', '.join(unfinished_phases)}"
        return Response(
            {"error": error_message}, status=status.HTTP_406_NOT_ACCEPTABLE
        )

    if not settings.DEBUG:
        try:
            evalai_api_server = settings.EVALAI_API_SERVER
            approval_webhook_url = settings.APPROVAL_WEBHOOK_URL

            if not evalai_api_server:
                raise ValueError(
                    "EVALAI_API_SERVER environment variable is missing."
                )
            if not approval_webhook_url:
                raise ValueError(
                    "APPROVAL_WEBHOOK_URL environment variable is missing."
                )
        except:  # noqa: E722
            error_message = "Sorry, there was an error fetching required data for approval requests."
            return Response(
                {"error": error_message}, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        message = {
            "text": f"Challenge {challenge_pk} has finished submissions and has requested for approval!",
            "fields": [
                {
                    "title": "Admin URL",
                    "value": f"{evalai_api_server}/api/admin/challenges/challenge/{challenge_pk}",
                    "short": False,
                },
                {
                    "title": "Challenge title",
                    "value": challenge.title,
                    "short": False,
                },
            ],
        }

        webhook_response = send_slack_notification(
            webhook=approval_webhook_url, message=message
        )
        if webhook_response:
            if webhook_response.content.decode("utf-8") == "ok":
                response_data = {
                    "message": "Approval request sent!",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                error_message = f"Sorry, there was an error sending approval request: {str(webhook_response.content.decode('utf-8'))}. Please try again."
                return Response(
                    {"error": error_message},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
        else:
            error_message = "Sorry, there was an error sending approval request: No response received. Please try again."
            return Response(
                {"error": error_message}, status=status.HTTP_406_NOT_ACCEPTABLE
            )
    else:
        error_message = (
            "Please approve the challenge using admin for local deployments."
        )
        return Response(
            {"error": error_message}, status=status.HTTP_406_NOT_ACCEPTABLE
        )


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_leaderboard_data(request, challenge_phase_split_pk):
    """
    API to get leaderboard data for a challenge phase split
    Arguments:
        challenge_phase_split {int} -- Challenge phase split primary key
    Returns:
        {dict} -- Response object
    """
    if not is_user_a_staff(request.user):
        response_data = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
    try:
        challenge_phase_split = get_challenge_phase_split_model(
            challenge_phase_split_pk
        )
        leaderboard_data = LeaderboardData.objects.filter(
            challenge_phase_split=challenge_phase_split, is_disabled=False
        )
    except LeaderboardData.DoesNotExist:
        response_data = {"error": "Leaderboard data not found!"}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    serializer = LeaderboardDataSerializer(
        leaderboard_data, context={"request": request}, many=True
    )
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_challenge_approval(request):
    """
    API to update challenge
    Arguments:
        request {dict} -- Request object

    Query Parameters:
        challenge_pk {int} -- Challenge primary key
        approved_by_admin {bool} -- Challenge approved by admin
    """
    if not is_user_a_staff(request.user):
        response_data = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    challenge_pk = request.data.get("challenge_pk")
    approved_by_admin = request.data.get("approved_by_admin")
    if not challenge_pk:
        response_data = {"error": "Challenge primary key is missing!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    if not approved_by_admin:
        response_data = {"error": "approved_by_admin is missing!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    try:
        challenge = get_challenge_model(challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge not found!"}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    challenge.approved_by_admin = approved_by_admin
    try:
        challenge.save()
    except Exception as e:  # noqa: E722
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    response_data = {"message": "Challenge updated successfully!"}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_challenge_attributes(request):
    """
    API to update attributes of the Challenge model
    Arguments:
        request {dict} -- Request object

    Query Parameters:
        challenge_pk {int} -- Challenge primary key
        **kwargs {any} -- Key-value pairs representing attributes and their new values
    """
    if not request.user.is_staff:
        response_data = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    challenge_pk = request.data.get("challenge_pk")

    if not challenge_pk:
        response_data = {"error": "Challenge primary key is missing!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {
            "error": f"Challenge with primary key {challenge_pk} not found!"
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    # Update attributes based on the request data
    for key, value in request.data.items():
        if key != "challenge_pk" and hasattr(challenge, key):
            setattr(challenge, key, value)

    try:
        challenge.save()
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response_data = {
        "message": f"Challenge attributes updated successfully for challenge with primary key {challenge_pk}!"
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def modify_leaderboard_data(request):
    """
    API to update leaderboard data
    Arguments:
        request {dict} -- Request object
    Query Parameters:
        leaderboard_data {list} -- List of leaderboard data
        challenge_phase_split {int} -- Challenge phase split primary key
        submission {int} -- Submission primary key
        leaderboard {int} -- Leaderboard primary key
        is_disabled {int} -- Leaderboard data is disabled
    """
    if not is_user_a_staff(request.user):
        response_data = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == "PUT":
        leaderboard_data_pk = request.data.get("leaderboard_data")
        leaderboard_pk = request.data.get("leaderboard")
        challenge_phase_split_pk = request.data.get("challenge_phase_split")
        submission_pk = request.data.get("submission")
        is_disabled = request.data.get("is_disabled")

        # Perform lookups and handle errors
        try:
            if leaderboard_data_pk:
                leaderboard_data = LeaderboardData.objects.get(
                    pk=leaderboard_data_pk
                )
            else:
                submission = get_submission_model(submission_pk)
                challenge_phase_split = get_challenge_phase_split_model(
                    challenge_phase_split_pk
                )
                leaderboard = get_leaderboard_model(leaderboard_pk)
                leaderboard_data = LeaderboardData.objects.get(
                    submission=submission,
                    challenge_phase_split=challenge_phase_split,
                    leaderboard=leaderboard,
                )
        except Exception:
            response_data = {"error": "Resource not found!"}
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        # Update the 'is_disabled' attribute
        leaderboard_data.is_disabled = bool(int(is_disabled))
        leaderboard_data.save()

        # Serialize and return the updated data
        response_data = {"message": "Leaderboard data updated successfully!"}
        return Response(response_data, status=status.HTTP_200_OK)
