import botocore
import datetime
import json
import logging
import os
import uuid

from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.utils import timezone
from django.db.models import Q

from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from accounts.permissions import HasVerifiedEmail
from base.utils import (
    StandardResultSetPagination,
    get_boto3_client,
    get_or_create_sqs_queue,
    paginated_queryset,
    is_user_a_staff,
)
from challenges.models import (
    ChallengePhase,
    Challenge,
    ChallengeEvaluationCluster,
    ChallengePhaseSplit,
    LeaderboardData,
)
from challenges.utils import (
    complete_s3_multipart_file_upload,
    generate_presigned_url_for_multipart_upload,
    get_aws_credentials_for_challenge,
    get_challenge_model,
    get_challenge_phase_model,
    get_challenge_phase_split_model,
    get_participant_model,
)
from hosts.models import ChallengeHost
from hosts.utils import is_user_a_host_of_challenge, is_user_a_staff_or_host
from participants.models import ParticipantTeam
from participants.utils import (
    get_participant_team_model,
    get_participant_team_id_of_user_for_a_challenge,
    get_participant_team_of_user_for_a_challenge,
    is_user_part_of_participant_team,
)
from .aws_utils import generate_aws_eks_bearer_token
from .filters import SubmissionFilter
from .models import Submission
from .sender import publish_submission_message
from .serializers import (
    CreateLeaderboardDataSerializer,
    LeaderboardDataSerializer,
    RemainingSubmissionDataSerializer,
    SubmissionSerializer,
)
from .tasks import download_file_and_publish_submission_message
from .utils import (
    calculate_distinct_sorted_leaderboard_data,
    get_leaderboard_data_model,
    get_remaining_submission_for_a_phase,
    get_submission_model,
    handle_submission_rerun,
    handle_submission_resume,
    is_url_valid,
    reorder_submissions_comparator,
    reorder_submissions_comparator_to_key,
)

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    methods=["post"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        ),
        openapi.Parameter(
            name="challenge_phase_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge Phase ID",
            required=True,
        ),
    ],
    responses={status.HTTP_201_CREATED: openapi.Response("")},
)
@swagger_auto_schema(
    methods=["get"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        ),
        openapi.Parameter(
            name="challenge_phase_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge Phase ID",
            required=True,
        ),
    ],
    responses={status.HTTP_201_CREATED: openapi.Response("")},
)
@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def challenge_submission(request, challenge_id, challenge_phase_id):
    """API Endpoint for making a submission to a challenge"""

    # check if the challenge exists or not
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist:
        response_data = {"error": "Challenge does not exist"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # check if the challenge phase exists or not
    try:
        challenge_phase = ChallengePhase.objects.get(
            pk=challenge_phase_id, challenge=challenge
        )
    except ChallengePhase.DoesNotExist:
        response_data = {"error": "Challenge Phase does not exist"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        # getting participant team object for the user for a particular challenge.
        participant_team_id = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_id
        )

        # check if participant team exists or not.
        try:
            ParticipantTeam.objects.get(pk=participant_team_id)
        except ParticipantTeam.DoesNotExist:
            response_data = {
                "error": "You haven't participated in the challenge"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        submission = Submission.objects.filter(
            participant_team=participant_team_id,
            challenge_phase=challenge_phase,
            ignore_submission=False,
        ).order_by("-submitted_at")
        filtered_submissions = SubmissionFilter(
            request.GET, queryset=submission
        )
        # rerank in progress submissions in ascending order of submitted_at
        reordered_submissions = sorted(
            filtered_submissions.qs,
            key=reorder_submissions_comparator_to_key(
                reorder_submissions_comparator
            ),
        )
        paginator, result_page = paginated_queryset(
            reordered_submissions, request
        )
        serializer = SubmissionSerializer(
            result_page, many=True, context={"request": request}
        )
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == "POST":

        # check if the challenge is active or not
        if not challenge.is_active:
            response_data = {"error": "Challenge is not active"}
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        # check if challenge phase is active
        if not challenge_phase.is_active:
            response_data = {
                "error": "Sorry, cannot accept submissions since challenge phase is not active"
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        # check if user is a challenge host or a participant
        if not is_user_a_host_of_challenge(request.user, challenge_id):
            # check if challenge phase is public and accepting solutions
            if not challenge_phase.is_public:
                response_data = {
                    "error": "Sorry, cannot accept submissions since challenge phase is not public"
                }
                return Response(
                    response_data, status=status.HTTP_403_FORBIDDEN
                )

            # if allowed email ids list exist, check if the user exist in that list or not
            if challenge_phase.allowed_email_ids:
                if request.user.email not in challenge_phase.allowed_email_ids:
                    response_data = {
                        "error": "Sorry, you are not allowed to participate in this challenge phase"
                    }
                    return Response(
                        response_data, status=status.HTTP_403_FORBIDDEN
                    )

        participant_team_id = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_id
        )
        try:
            participant_team = ParticipantTeam.objects.get(
                pk=participant_team_id
            )
        except ParticipantTeam.DoesNotExist:
            response_data = {
                "error": "You haven't participated in the challenge"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        # check if manual approval is enabled and team is approved
        if challenge.manual_participant_approval and not challenge.approved_participant_teams.filter(pk=participant_team_id).exists():
            response_data = {
                "error": "Your team is not approved by challenge host"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        all_participants_email = participant_team.get_all_participants_email()
        for participant_email in all_participants_email:
            if participant_email in challenge.banned_email_ids:
                message = "You're a part of {} team and it has been banned from this challenge. \
                Please contact the challenge host.".format(
                    participant_team.team_name
                )
                response_data = {"error": message}
                return Response(
                    response_data, status=status.HTTP_403_FORBIDDEN
                )

        # Fetch the number of submissions under progress.
        submissions_in_progress_status = [
            Submission.SUBMITTED,
            Submission.SUBMITTING,
            Submission.RESUMING,
            Submission.QUEUED,
            Submission.RUNNING,
        ]
        submissions_in_progress = Submission.objects.filter(
            participant_team=participant_team_id,
            challenge_phase=challenge_phase,
            status__in=submissions_in_progress_status,
        ).count()

        if (
            submissions_in_progress
            >= challenge_phase.max_concurrent_submissions_allowed
        ):
            message = "You have {} submissions that are being processed. \
                       Please wait for them to finish and then try again."
            response_data = {"error": message.format(submissions_in_progress)}
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        if not request.FILES:
            if request.data.get("file_url") is None:
                response_data = {"error": "The file URL is missing!"}
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )
            if not is_url_valid(request.data["file_url"]):
                response_data = {"error": "The file URL does not exists!"}
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )
            download_file_and_publish_submission_message.delay(
                request.data,
                request.user.id,
                request.method,
                challenge_phase_id,
            )
            response_data = {
                "message": "Please wait while your submission being evaluated!"
            }
            return Response(response_data, status=status.HTTP_200_OK)

        if request.data.get("submission_meta_attributes"):
            submission_meta_attributes = json.load(
                request.data.get("submission_meta_attributes")
            )
            request.data[
                "submission_meta_attributes"
            ] = submission_meta_attributes

        if request.data.get("is_public") is None:
            request.data["is_public"] = (
                True if challenge_phase.is_submission_public else False
            )
        else:
            request.data["is_public"] = json.loads(request.data["is_public"])
            if (
                request.data.get("is_public")
                and challenge_phase.is_restricted_to_select_one_submission
            ):
                # Handle corner case for restrict one public lb submission
                submissions_already_public = Submission.objects.filter(
                    is_public=True,
                    participant_team=participant_team,
                    challenge_phase=challenge_phase,
                )
                # Make the existing public submission private before making the new submission public
                if submissions_already_public.count() == 1:
                    # Case when the phase is restricted to make only one submission as public
                    submission_serializer = SubmissionSerializer(
                        submissions_already_public[0],
                        data={"is_public": False},
                        context={
                            "participant_team": participant_team,
                            "challenge_phase": challenge_phase,
                            "request": request,
                        },
                        partial=True,
                    )
                    if submission_serializer.is_valid():
                        submission_serializer.save()

        # Override submission visibility if leaderboard_public = False for a challenge phase
        if not challenge_phase.leaderboard_public:
            request.data["is_public"] = challenge_phase.is_submission_public

        serializer = SubmissionSerializer(
            data=request.data,
            context={
                "participant_team": participant_team,
                "challenge_phase": challenge_phase,
                "request": request,
            },
        )
        message = {
            "challenge_pk": challenge_id,
            "phase_pk": challenge_phase_id,
            "is_static_dataset_code_upload_submission": False,
        }
        if challenge.is_docker_based:
            try:
                file_content = json.loads(request.FILES["input_file"].read())
                message["submitted_image_uri"] = file_content[
                    "submitted_image_uri"
                ]
                if challenge.is_static_dataset_code_upload:
                    message["is_static_dataset_code_upload_submission"] = True
            except Exception as ex:
                response_data = {
                    "error": "Error {} in submitted_image_uri from submission file".format(
                        ex
                    )
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            submission = serializer.instance
            message["submission_pk"] = submission.id
            # publish message in the queue
            publish_submission_message(message)
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE
        )


@api_view(["PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def change_submission_data_and_visibility(
    request, challenge_pk, challenge_phase_pk, submission_pk
):
    """
    API Endpoint for updating the submission meta data
    and changing submission visibility.
    """

    # check if the challenge exists or not
    challenge = get_challenge_model(challenge_pk)

    # check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    if not challenge.is_active:
        response_data = {"error": "Challenge is not active"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    # check if challenge phase is public and accepting solutions
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        if not challenge_phase.is_public:
            response_data = {
                "error": "Sorry, cannot accept submissions since challenge phase is not public"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)
        elif request.data.get("is_baseline"):
            response_data = {
                "error": "Sorry, you are not authorized to make this request"
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge_pk
    )

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "You haven't participated in the challenge"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = Submission.objects.get(
            participant_team=participant_team,
            challenge_phase=challenge_phase,
            id=submission_pk,
        )
    except Submission.DoesNotExist:
        response_data = {"error": "Submission does not exist"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        is_public = request.data["is_public"]
        if is_public is True:
            when_made_public = datetime.datetime.now()
            request.data["when_made_public"] = when_made_public

            submissions_already_public = Submission.objects.filter(
                is_public=True,
                participant_team=participant_team,
                challenge_phase=challenge_phase,
            )
            # Make the existing public submission private before making the new submission public
            if (
                challenge_phase.is_restricted_to_select_one_submission
                and is_public
                and submissions_already_public.count() == 1
            ):
                # Case when the phase is restricted to make only one submission as public
                submission_serializer = SubmissionSerializer(
                    submissions_already_public[0],
                    data={"is_public": False},
                    context={
                        "participant_team": participant_team,
                        "challenge_phase": challenge_phase,
                        "request": request,
                    },
                    partial=True,
                )
                if submission_serializer.is_valid():
                    submission_serializer.save()
    except KeyError:
        pass

    serializer = SubmissionSerializer(
        submission,
        data=request.data,
        context={
            "participant_team": participant_team,
            "challenge_phase": challenge_phase,
            "request": request,
        },
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    methods=["get"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_phase_split_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge Phase Split ID",
            required=True,
        )
    ],
    operation_id="leaderboard",
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Count of values on the leaderboard",
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
                                "submission__participant_team__team_name": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Participant Team Name",
                                ),
                                "challenge_phase_split": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Challenge Phase Split ID",
                                ),
                                "filtering_score": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Default filtering score for results",
                                ),
                                "leaderboard__schema": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Leaderboard Schema of the corresponding challenge",
                                ),
                                "result": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Leaderboard Metrics values according to leaderboard schema",
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT
                                    ),
                                ),
                                "submission__submitted_at": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Time stamp when submission was submitted at",
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
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def leaderboard(request, challenge_phase_split_id):
    """
    Returns leaderboard for a corresponding Challenge Phase Split

    - Arguments:
        ``challenge_phase_split_id``: Primary key for the challenge phase split for which leaderboard is to be fetched

    - Returns:
        Leaderboard entry objects in a list
    """

    # check if the challenge exists or not
    challenge_phase_split = get_challenge_phase_split_model(
        challenge_phase_split_id
    )
    challenge_obj = challenge_phase_split.challenge_phase.challenge
    order_by = request.GET.get("order_by")
    (
        response_data,
        http_status_code,
    ) = calculate_distinct_sorted_leaderboard_data(
        request.user,
        challenge_obj,
        challenge_phase_split,
        only_public_entries=True,
        order_by=order_by,
    )
    # The response 400 will be returned if the leaderboard isn't public or `default_order_by` key is missing in leaderboard.
    if http_status_code == status.HTTP_400_BAD_REQUEST:
        return Response(response_data, status=http_status_code)

    paginator, result_page = paginated_queryset(
        response_data, request, pagination_class=StandardResultSetPagination()
    )
    response_data = result_page
    return paginator.get_paginated_response(response_data)


@swagger_auto_schema(
    methods=["get"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_phase_split_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge Phase Split Primary Key",
            required=True,
        )
    ],
    operation_id="get_all_entries_on_public_leaderboard",
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Count of values on the leaderboard",
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
                                    type=openapi.TYPE_STRING,
                                    description="Result ID",
                                ),
                                "submission__participant_team": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Participant Team ID",
                                ),
                                "submission__participant_team__team_name": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Participant Team Name",
                                ),
                                "submission__participant_team__team_url": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Participant Team URL",
                                ),
                                "submission__is_baseline": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Boolean to decide if submission is baseline",
                                ),
                                "submission__is_public": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Boolean to decide if submission is public",
                                ),
                                "challenge_phase_split": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Challenge Phase Split ID",
                                ),
                                "result": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Leaderboard Metrics values according to leaderboard schema",
                                    items=openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                ),
                                "error": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Error returned for the result",
                                ),
                                "leaderboard__schema": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Leaderboard Schema of the corresponding challenge",
                                    properties={
                                        "labels": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            description="Labels of leaderboard schema",
                                            items=openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                        ),
                                        "default_order_by": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Default ordering label for the leaderboard schema",
                                        ),
                                    },
                                ),
                                "submission__submitted_at": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Time stamp when submission was submitted at",
                                ),
                                "submission__method_name": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Method of submission",
                                ),
                                "submission__id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="ID of submission",
                                ),
                                "submission__submission_metadata": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Metadata and other info about submission",
                                ),
                                "filtering_score": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Default filtering score for results",
                                ),
                                "filtering_error": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Default filtering error for results",
                                ),
                            },
                        ),
                    ),
                },
            ),
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_all_entries_on_public_leaderboard(request, challenge_phase_split_pk):
    """
    Returns public/private leaderboard entries to corresponding challenge phase split for a challenge host

    - Arguments:
        ``challenge_phase_split_pk``: Primary key for the challenge phase split for which leaderboard is to be fetched

    - Returns:
        All Leaderboard entry objects in a list

    Below is the sample response returned by the API

    ```
    {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "submission__participant_team": 2,
            "submission__participant_team__team_name": "Sanchezview Participant Team",
            "submission__participant_team__team_url": "",
            "submission__is_baseline": true,
            "submission__is_public": true,
            "challenge_phase_split": 1,
            "result": [
                26
            ],
            "error": null,
            "leaderboard__schema": {
                "labels": [
                    "score"
                ],
                "default_order_by": "score"
            },
            "submission__submitted_at": "2021-01-12T10:14:58.764572Z",
            "submission__method_name": "Vernon",
            "submission__id": 10,
            "submission__submission_metadata": null,
            "filtering_score": 26.0,
            "filtering_error": 0
        }
    ]
    }
    ```
    """
    # check if the challenge exists or not
    challenge_phase_split = get_challenge_phase_split_model(
        challenge_phase_split_pk
    )

    challenge_obj = challenge_phase_split.challenge_phase.challenge

    # Allow access only to challenge host
    if not is_user_a_staff_or_host(request.user, challenge_obj.pk):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    order_by = request.GET.get("order_by")
    (
        response_data,
        http_status_code,
    ) = calculate_distinct_sorted_leaderboard_data(
        request.user,
        challenge_obj,
        challenge_phase_split,
        only_public_entries=False,
        order_by=order_by,
    )
    # The response 400 will be returned if the leaderboard isn't public or `default_order_by` key is missing in leaderboard.
    if http_status_code == status.HTTP_400_BAD_REQUEST:
        return Response(response_data, status=http_status_code)

    paginator, result_page = paginated_queryset(
        response_data, request, pagination_class=StandardResultSetPagination()
    )
    response_data = result_page
    return paginator.get_paginated_response(response_data)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_remaining_submissions(request, challenge_pk):
    """
    API to get the number of remaining submission for all phases.
    Below is the sample response returned by the API

    {
        "participant_team": "Sample_Participant_Team",
        "participant_team_id": 2,
        "phases": [
            {
                "id": 1,
                "slug": "megan-phase-1",
                "name": "Megan Phase",
                "start_date": "2018-10-28T14:22:53.022639Z",
                "end_date": "2020-06-19T14:22:53.022660Z",
                "limits": {
                    "remaining_submissions_this_month_count": 9,
                    "remaining_submissions_today_count": 5,
                    "remaining_submissions_count": 29
                }
            },
            {
                "id": 2,
                "slug": "molly-phase-2",
                "name": "Molly Phase",
                "start_date": "2018-10-28T14:22:53Z",
                "end_date": "2020-06-19T14:22:53Z",
                "limits": {
                    "message": "You have exhausted this month's submission limit!",
                    "remaining_time": "1481076.929224"  // remaining_time is in seconds
                }
            }
        ]
    }
    """
    phases_data = {}
    challenge = get_challenge_model(challenge_pk)
    challenge_phases = ChallengePhase.objects.filter(
        challenge=challenge
    ).order_by("pk")
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        challenge_phases = challenge_phases.filter(
            challenge=challenge, is_public=True
        ).order_by("pk")
    phase_data_list = list()
    for phase in challenge_phases:
        (
            remaining_submission_message,
            response_status,
        ) = get_remaining_submission_for_a_phase(
            request.user, phase.id, challenge_pk
        )
        if response_status != status.HTTP_200_OK:
            return Response(
                remaining_submission_message, status=response_status
            )
        phase_data_list.append(
            RemainingSubmissionDataSerializer(
                phase, context={"limits": remaining_submission_message}
            ).data
        )
    phases_data["phases"] = phase_data_list
    participant_team = get_participant_team_of_user_for_a_challenge(
        request.user, challenge_pk
    )
    phases_data["participant_team"] = participant_team.team_name
    phases_data["participant_team_id"] = participant_team.id
    return Response(phases_data, status=status.HTTP_200_OK)


@api_view(["GET", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_submission_by_pk(request, submission_id):
    """
    API endpoint to fetch the details of a submission.
    Only the submission owner or the challenge hosts are allowed.
    """
    try:
        submission = Submission.objects.get(pk=submission_id)
    except Submission.DoesNotExist:
        response_data = {
            "error": "Submission {} does not exist".format(submission_id)
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    host_team = submission.challenge_phase.challenge.creator
    if (
        request.user.id == submission.created_by.id
        or ChallengeHost.objects.filter(
            user=request.user.id, team_name__pk=host_team.pk
        ).exists()
    ):
        if request.method == "GET":
            serializer = SubmissionSerializer(
                submission, context={"request": request}
            )
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            serializer = SubmissionSerializer(
                submission,
                data=request.data,
                context={"ignore_submission": True, "request": request},
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                response_data = serializer.data
                return Response(response_data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
    response_data = {
        "error": "Sorry, you are not authorized to access this submission."
    }
    return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(
    methods=["put"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        )
    ],
    operation_id="update_submission",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "challenge_phase": openapi.Schema(
                type=openapi.TYPE_STRING, description="Challenge Phase ID"
            ),
            "submission": openapi.Schema(
                type=openapi.TYPE_STRING, description="Submission ID"
            ),
            "stdout": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Submission output file content",
            ),
            "stderr": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Submission error file content",
            ),
            "submission_status": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Final status of submission (can take one of these values): CANCELLED/FAILED/FINISHED",
            ),
            "result": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Submission results in array format."
                " API will throw an error if any split and/or metric is missing)",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "split1": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="dataset split 1 codename",
                        ),
                        "show_to_participant": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Boolean to decide if the results are shown to participant or not",
                        ),
                        "accuracies": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Accuracies on different metrics",
                            properties={
                                "metric1": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Numeric accuracy on metric 1",
                                ),
                                "metric2": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Numeric accuracy on metric 2",
                                ),
                            },
                        ),
                    },
                ),
            ),
            "metadata": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="It contains the metadata related to submission (only visible to challenge hosts)",
                properties={
                    "foo": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Some data relevant to key",
                    )
                },
            ),
        },
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            "{'success': 'Submission result has been successfully updated'}"
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@swagger_auto_schema(
    methods=["patch"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        )
    ],
    operation_id="update_submission",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "submission": openapi.Schema(
                type=openapi.TYPE_STRING, description="Submission ID"
            ),
            "job_name": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Job name for the running submission",
            ),
            "submission_status": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Updated status of submission from submitted i.e. RUNNING",
            ),
        },
    ),
    responses={
        status.HTTP_200_OK: openapi.Response("{<updated submission-data>}"),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@api_view(["PUT", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_submission(request, challenge_pk):
    """
    API endpoint to update submission related attributes

    Query Parameters:

     - ``challenge_phase``: challenge phase id, e.g. 123 (**required**)
     - ``submission``: submission id, e.g. 123 (**required**)
     - ``stdout``: Stdout after evaluation, e.g. "Evaluation completed in 2 minutes" (**required**)
     - ``stderr``: Stderr after evaluation, e.g. "Failed due to incorrect file format" (**required**)
     - ``environment_log``: Environment error after evaluation, e.g. "Failed due to attempted action being invalid" (**code upload challenge only**)
     - ``submission_status``: Status of submission after evaluation
        (can take one of the following values: `FINISHED`/`CANCELLED`/`FAILED`), e.g. FINISHED (**required**)
     - ``result``: contains accuracies for each metric, (**required**) e.g.
            [
                {
                    "split": "split1-codename",
                    "show_to_participant": True,
                    "accuracies": {
                        "metric1": 90
                    }
                },
                {
                    "split": "split2-codename",
                    "show_to_participant": False,
                    "accuracies": {
                        "metric1": 50,
                        "metric2": 40
                    }
                }
            ]
     - ``metadata``: Contains the metadata related to submission (only visible to challenge hosts) e.g:
            {
                "average-evaluation-time": "5 sec",
                "foo": "bar"
            }
    """
    if not is_user_a_staff(request.user) and not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "PUT":
        challenge_phase_pk = request.data.get("challenge_phase")
        submission_pk = request.data.get("submission")
        submission_status = request.data.get("submission_status", "").lower()
        stdout_content = request.data.get("stdout", "").encode("utf-8")
        stderr_content = request.data.get("stderr", "").encode("utf-8")
        environment_log_content = request.data.get("environment_log", "").encode("utf-8")
        submission_result = request.data.get("result", "")
        metadata = request.data.get("metadata", "")
        submission = get_submission_model(submission_pk)

        public_results = []
        successful_submission = (
            True if submission_status == Submission.FINISHED else False
        )
        if submission_status not in [
            Submission.FAILED,
            Submission.CANCELLED,
            Submission.FINISHED,
        ]:
            response_data = {"error": "Sorry, submission status is invalid"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if successful_submission:
            try:
                results = json.loads(submission_result)
            except (ValueError, TypeError) as exc:
                response_data = {
                    "error": "`result` key contains invalid data with error {}."
                    "Please try again with correct format.".format(str(exc))
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

            leaderboard_data_list = []
            for phase_result in results:
                split = phase_result.get("split")
                accuracies = phase_result.get("accuracies")
                show_to_participant = phase_result.get(
                    "show_to_participant", False
                )
                try:
                    challenge_phase_split = ChallengePhaseSplit.objects.get(
                        challenge_phase__pk=challenge_phase_pk,
                        dataset_split__codename=split,
                    )
                except ChallengePhaseSplit.DoesNotExist:
                    response_data = {
                        "error": "Challenge Phase Split does not exist with phase_id: {} and"
                        "split codename: {}".format(challenge_phase_pk, split)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                leaderboard_metrics = (
                    challenge_phase_split.leaderboard.schema.get("labels")
                )
                missing_metrics = []
                malformed_metrics = []
                for metric, value in accuracies.items():
                    if metric not in leaderboard_metrics:
                        missing_metrics.append(metric)

                    if not (
                        isinstance(value, float) or isinstance(value, int)
                    ):
                        malformed_metrics.append((metric, type(value)))

                if len(missing_metrics):
                    response_data = {
                        "error": "Following metrics are missing in the"
                        "leaderboard data: {}".format(missing_metrics)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                if len(malformed_metrics):
                    response_data = {
                        "error": "Values for following metrics are not of"
                        "float/int: {}".format(malformed_metrics)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    leaderboard_data = get_leaderboard_data_model(
                        submission_pk, challenge_phase_split.pk
                    )
                except LeaderboardData.DoesNotExist:
                    leaderboard_data = None

                data = {"result": accuracies}
                if leaderboard_data is not None:
                    serializer = CreateLeaderboardDataSerializer(
                        leaderboard_data,
                        data=data,
                        partial=True,
                        context={
                            "challenge_phase_split": challenge_phase_split,
                            "submission": submission,
                            "request": request,
                        },
                    )
                else:
                    serializer = CreateLeaderboardDataSerializer(
                        data=data,
                        context={
                            "challenge_phase_split": challenge_phase_split,
                            "submission": submission,
                            "request": request,
                        },
                    )
                if serializer.is_valid():
                    leaderboard_data_list.append(serializer)
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                # Only after checking if the serializer is valid, append the public split results to results file
                if show_to_participant:
                    public_results.append(accuracies)

            try:
                with transaction.atomic():
                    for serializer in leaderboard_data_list:
                        serializer.save()
            except IntegrityError:
                logger.exception(
                    "Failed to update submission_id {} related metadata".format(
                        submission_pk
                    )
                )
                response_data = {
                    "error": "Failed to update submission_id {} related metadata".format(
                        submission_pk
                    )
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

        submission.status = submission_status
        submission.completed_at = timezone.now()
        submission.stdout_file.save("stdout.txt", ContentFile(stdout_content))
        submission.stderr_file.save("stderr.txt", ContentFile(stderr_content))
        submission.environment_log_file.save("environment_log.txt", ContentFile(environment_log_content))
        submission.submission_result_file.save(
            "submission_result.json", ContentFile(str(public_results))
        )
        submission.submission_metadata_file.save(
            "submission_metadata_file.json", ContentFile(str(metadata))
        )
        submission.save()
        response_data = {
            "success": "Submission result has been successfully updated"
        }
        return Response(response_data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        submission_pk = request.data.get("submission")
        submission = get_submission_model(submission_pk)
        # Update submission_input_file for is_static_dataset_code_upload submission evaluation
        if (
            request.FILES.get("submission_input_file")
            and submission.challenge_phase.challenge.is_static_dataset_code_upload
        ):
            serializer = SubmissionSerializer(
                submission,
                data=request.data,
                context={
                    "request": request,
                },
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                message = {
                    "challenge_pk": challenge_pk,
                    "phase_pk": submission.challenge_phase.pk,
                    "submission_pk": submission_pk,
                    "is_static_dataset_code_upload_submission": False,
                }
                # publish message in the queue
                publish_submission_message(message)
                response_data = serializer.data
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
        submission_status = request.data.get("submission_status", "").lower()
        job_name = request.data.get("job_name", "").lower()
        jobs = submission.job_name
        if job_name:
            jobs.append(job_name)
        if submission_status not in [Submission.QUEUED, Submission.RUNNING]:
            response_data = {"error": "Sorry, submission status is invalid"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "status": submission_status,
            "started_at": str(timezone.now()),
            "job_name": jobs,
        }
        serializer = SubmissionSerializer(
            submission, data=data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    methods=["put"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        )
    ],
    operation_id="update_submission",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "challenge_phase": openapi.Schema(
                type=openapi.TYPE_STRING, description="Challenge Phase ID"
            ),
            "submission": openapi.Schema(
                type=openapi.TYPE_STRING, description="Submission ID"
            ),
            "stdout": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Submission output file content",
            ),
            "stderr": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Submission error file content",
            ),
            "submission_status": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Final status of submission (can take one of these values): CANCELLED/FAILED/FINISHED",
            ),
            "result": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Submission results in array format."
                " API will throw an error if any split and/or metric is missing)",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "split1": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="dataset split 1 codename",
                        ),
                        "show_to_participant": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Boolean to decide if the results are shown to participant or not",
                        ),
                        "accuracies": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Accuracies on different metrics",
                            properties={
                                "metric1": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Numeric accuracy on metric 1",
                                ),
                                "metric2": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Numeric accuracy on metric 2",
                                ),
                            },
                        ),
                    },
                ),
            ),
            "metadata": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="It contains the metadata related to submission (only visible to challenge hosts)",
                properties={
                    "foo": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Some data relevant to key",
                    )
                },
            ),
        },
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            "{'success': 'Submission result has been successfully updated'}"
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@swagger_auto_schema(
    methods=["patch"],
    manual_parameters=[
        openapi.Parameter(
            name="challenge_pk",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Challenge ID",
            required=True,
        )
    ],
    operation_id="update_submission",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "submission": openapi.Schema(
                type=openapi.TYPE_STRING, description="Submission ID"
            ),
            "job_name": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Job name for the running submission",
            ),
            "submission_status": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Updated status of submission from submitted i.e. RUNNING",
            ),
        },
    ),
    responses={
        status.HTTP_200_OK: openapi.Response("{<updated submission-data>}"),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@api_view(["PUT", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_partially_evaluated_submission(request, challenge_pk):
    """
    API endpoint to update submission related attributes

    Query Parameters:

     - ``challenge_phase``: challenge phase id, e.g. 123 (**required**)
     - ``submission``: submission id, e.g. 123 (**required**)
     - ``stdout``: Stdout after evaluation, e.g. "Evaluation completed in 2 minutes" (**required**)
     - ``stderr``: Stderr after evaluation, e.g. "Failed due to incorrect file format" (**required**)
     - ``submission_status``: Status of submission after evaluation
        (can take one of the following values: `FINISHED`/`CANCELLED`/`FAILED`/`PARTIALLY_EVALUATED`),
        e.g. FINISHED (**required**)
     - ``result``: contains accuracies for each metric, (**required**) e.g.
            [
                {
                    "split": "split1-codename",
                    "show_to_participant": True,
                    "accuracies": {
                        "metric1": 90
                    }
                },
                {
                    "split": "split2-codename",
                    "show_to_participant": False,
                    "accuracies": {
                        "metric1": 50,
                        "metric2": 40
                    }
                }
            ]
     - ``metadata``: Contains the metadata related to submission (only visible to challenge hosts) e.g:
            {
                "average-evaluation-time": "5 sec",
                "foo": "bar"
            }
    """
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "PUT":
        challenge_phase_pk = request.data.get("challenge_phase")
        submission_pk = request.data.get("submission")
        submission_status = request.data.get("submission_status", "").lower()
        stdout_content = request.data.get("stdout", "")
        stderr_content = request.data.get("stderr", "")
        submission_result = request.data.get("result", "")
        metadata = request.data.get("metadata", "")
        submission = get_submission_model(submission_pk)

        public_results = []
        successful_submission = (
            True
            if (
                submission_status == Submission.FINISHED
                or submission_status == Submission.PARTIALLY_EVALUATED
            )
            else False
        )
        if submission_status not in [
            Submission.FAILED,
            Submission.CANCELLED,
            Submission.FINISHED,
            Submission.PARTIALLY_EVALUATED,
        ]:
            response_data = {"error": "Sorry, submission status is invalid"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if successful_submission:
            try:
                results = json.loads(submission_result)
            except (ValueError, TypeError) as exc:
                response_data = {
                    "error": "`result` key contains invalid data with error {}."
                    "Please try again with correct format.".format(str(exc))
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

            leaderboard_data_list = []
            for phase_result in results:
                split = phase_result.get("split")
                accuracies = phase_result.get("accuracies")
                show_to_participant = phase_result.get(
                    "show_to_participant", False
                )
                try:
                    challenge_phase_split = ChallengePhaseSplit.objects.get(
                        challenge_phase__pk=challenge_phase_pk,
                        dataset_split__codename=split,
                    )
                except ChallengePhaseSplit.DoesNotExist:
                    response_data = {
                        "error": "Challenge Phase Split does not exist with phase_id: {} and"
                        "split codename: {}".format(challenge_phase_pk, split)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                leaderboard_metrics = (
                    challenge_phase_split.leaderboard.schema.get("labels")
                )
                missing_metrics = []
                malformed_metrics = []
                for metric, value in accuracies.items():
                    if metric not in leaderboard_metrics:
                        missing_metrics.append(metric)

                    if not (
                        isinstance(value, float) or isinstance(value, int)
                    ):
                        malformed_metrics.append((metric, type(value)))

                is_partial_evaluation_phase = (
                    challenge_phase_split.challenge_phase.is_partial_submission_evaluation_enabled
                )
                if len(missing_metrics) and not is_partial_evaluation_phase:
                    response_data = {
                        "error": "Following metrics are missing in the"
                        "leaderboard data: {} of challenge phase: {}".format(
                            missing_metrics, challenge_phase_pk
                        )
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                if len(malformed_metrics):
                    response_data = {
                        "error": "Values for following metrics are not of"
                        "float/int: {}".format(malformed_metrics)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    leaderboard_data = get_leaderboard_data_model(
                        submission_pk, challenge_phase_split.pk
                    )
                except LeaderboardData.DoesNotExist:
                    leaderboard_data = None

                data = {"result": accuracies}
                if leaderboard_data is not None:
                    serializer = CreateLeaderboardDataSerializer(
                        leaderboard_data,
                        data=data,
                        partial=True,
                        context={
                            "challenge_phase_split": challenge_phase_split,
                            "submission": submission,
                            "request": request,
                        },
                    )
                else:
                    serializer = CreateLeaderboardDataSerializer(
                        data=data,
                        context={
                            "challenge_phase_split": challenge_phase_split,
                            "submission": submission,
                            "request": request,
                        },
                    )
                if serializer.is_valid():
                    leaderboard_data_list.append(serializer)
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                # Only after checking if the serializer is valid, append the public split results to results file
                if show_to_participant:
                    public_results.append(accuracies)

            try:
                with transaction.atomic():
                    for serializer in leaderboard_data_list:
                        serializer.save()
            except IntegrityError:
                logger.exception(
                    "Failed to update submission_id {} related metadata".format(
                        submission_pk
                    )
                )
                response_data = {
                    "error": "Failed to update submission_id {} related metadata".format(
                        submission_pk
                    )
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

        submission.status = submission_status
        submission.completed_at = timezone.now()
        submission.stdout_file.save("stdout.txt", ContentFile(stdout_content))
        submission.stderr_file.save("stderr.txt", ContentFile(stderr_content))
        submission.submission_result_file.save(
            "submission_result.json", ContentFile(str(public_results))
        )
        submission.submission_metadata_file.save(
            "submission_metadata_file.json", ContentFile(str(metadata))
        )
        submission.save()
        response_data = {
            "success": "Submission result has been successfully updated"
        }
        return Response(response_data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        submission_pk = request.data.get("submission")
        submission_status = request.data.get("submission_status", "").lower()
        job_name = request.data.get("job_name", "").lower()
        submission = get_submission_model(submission_pk)
        jobs = submission.job_name
        if job_name:
            jobs.append(job_name)
        if submission_status not in [
            Submission.RUNNING,
            Submission.PARTIALLY_EVALUATED,
            Submission.FINISHED,
        ]:
            response_data = {"error": "Sorry, submission status is invalid"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if submission_status == Submission.RUNNING:
            data = {
                "status": submission_status,
                "started_at": str(timezone.now()),
                "job_name": jobs,
            }
            serializer = SubmissionSerializer(
                submission,
                data=data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
        elif (
            submission_status == Submission.PARTIALLY_EVALUATED
            or submission_status == Submission.FINISHED
        ):
            challenge_phase_pk = request.data.get("challenge_phase")
            stdout_content = request.data.get("stdout", "")
            stderr_content = request.data.get("stderr", "")
            submission_result = request.data.get("result", "")

            try:
                results = json.loads(submission_result)
            except (ValueError, TypeError) as exc:
                response_data = {
                    "error": "`result` key contains invalid data with error {}."
                    "Please try again with correct format.".format(str(exc))
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

            public_results = []
            leaderboard_data_list = []
            for phase_result in results:
                split = phase_result.get("split")
                accuracies = phase_result.get("accuracies")
                show_to_participant = phase_result.get(
                    "show_to_participant", False
                )
                try:
                    challenge_phase_split = ChallengePhaseSplit.objects.get(
                        challenge_phase__pk=challenge_phase_pk,
                        dataset_split__codename=split,
                    )
                except ChallengePhaseSplit.DoesNotExist:
                    response_data = {
                        "error": "Challenge Phase Split does not exist with phase_id: {} and"
                        "split codename: {}".format(challenge_phase_pk, split)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    leaderboard_data = get_leaderboard_data_model(
                        submission_pk, challenge_phase_split.pk
                    )
                except LeaderboardData.DoesNotExist:
                    response_data = {
                        "error": "Leaderboard Data does not exist with phase_id: {} and"
                        "submission id: {}".format(
                            challenge_phase_pk, submission_pk
                        )
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                updated_result = leaderboard_data.result
                leaderboard_metrics = (
                    challenge_phase_split.leaderboard.schema.get("labels")
                )
                missing_metrics = []
                malformed_metrics = []
                for metric, value in accuracies.items():
                    if metric not in leaderboard_metrics:
                        missing_metrics.append(metric)

                    if not (
                        isinstance(value, float) or isinstance(value, int)
                    ):
                        malformed_metrics.append((metric, type(value)))
                    updated_result[metric] = value

                is_partial_evaluation_phase = (
                    challenge_phase_split.challenge_phase.is_partial_submission_evaluation_enabled
                )
                if len(missing_metrics) and not is_partial_evaluation_phase:
                    response_data = {
                        "error": "Following metrics are missing in the"
                        "leaderboard data: {} of challenge phase: {}".format(
                            missing_metrics, challenge_phase_pk
                        )
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                if len(malformed_metrics):
                    response_data = {
                        "error": "Values for following metrics are not of"
                        "float/int: {}".format(malformed_metrics)
                    }
                    return Response(
                        response_data, status=status.HTTP_400_BAD_REQUEST
                    )

                data = {"result": updated_result}
                serializer = CreateLeaderboardDataSerializer(
                    leaderboard_data,
                    data=data,
                    partial=True,
                    context={
                        "challenge_phase_split": challenge_phase_split,
                        "submission": submission,
                        "request": request,
                    },
                )
                if serializer.is_valid():
                    leaderboard_data_list.append(serializer)
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                # Only after checking if the serializer is valid, append the public split results to results file
                if show_to_participant:
                    public_results.append(accuracies)

            try:
                with transaction.atomic():
                    for serializer in leaderboard_data_list:
                        serializer.save()
            except IntegrityError:
                logger.exception(
                    "Failed to update submission_id {} related metadata".format(
                        submission_pk
                    )
                )
                response_data = {
                    "error": "Failed to update submission_id {} related metadata".format(
                        submission_pk
                    )
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

            submission.status = submission_status
            submission.completed_at = timezone.now()
            submission.stdout_file.save(
                "stdout.txt", ContentFile(stdout_content)
            )
            submission.stderr_file.save(
                "stderr.txt", ContentFile(stderr_content)
            )
            submission.submission_result_file.save(
                "submission_result.json", ContentFile(str(public_results))
            )
            submission.save()
            response_data = {
                "success": "Submission result has been successfully updated"
            }
            return Response(response_data, status=status.HTTP_200_OK)
        response_data = {"error": "Sorry, submission status is invalid"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def re_run_submission(request, submission_pk):
    """
    API endpoint to re-run a submission.
    Only challenge host has access to this endpoint by default.
    Participants can submit if the challenge allows.
    """
    try:
        submission = Submission.objects.get(pk=submission_pk)
    except Submission.DoesNotExist:
        response_data = {
            "error": "Submission {} does not exist".format(submission_pk)
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if submission.ignore_submission:
        response_data = {
            "error": "Deleted submissions can't be re-run"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # get the challenge and challenge phase object
    challenge_phase = submission.challenge_phase
    challenge = challenge_phase.challenge

    if not challenge.allow_participants_resubmissions and not is_user_a_staff_or_host(request.user, challenge.pk):
        response_data = {
            "error": "Only challenge hosts or admins are allowed to re-run a submission"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    if not challenge.is_active:
        response_data = {
            "error": "Challenge {} is not active".format(challenge.title)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    message = handle_submission_rerun(submission, Submission.CANCELLED)
    publish_submission_message(message)
    response_data = {
        "success": "Submission is successfully submitted for re-running"
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def resume_submission(request, submission_pk):
    """
    API endpoint to resume a submission from failed or partially evaluated state.
    Only challenge host has access to this endpoint.
    """
    try:
        submission = Submission.objects.get(pk=submission_pk)
    except Submission.DoesNotExist:
        response_data = {
            "error": "Submission {} does not exist".format(submission_pk)
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if submission.ignore_submission:
        response_data = {
            "error": "Deleted submissions can't be resumed"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if submission.status != Submission.FAILED:
        response_data = {
            "error": "Only failed submissions can be resumed"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if submission.status == Submission.RESUMING:
        response_data = {
            "error": "Submission is already resumed"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # get the challenge and challenge phase object
    challenge_phase = submission.challenge_phase
    challenge = challenge_phase.challenge

    if not challenge.allow_participants_resubmissions and not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Only challenge hosts are allowed to resume a submission"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    if not challenge.is_active:
        response_data = {
            "error": "Challenge {} is not active".format(challenge.title)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if not challenge.remote_evaluation:
        response_data = {
            "error": "Challenge {} is not remote. Resuming is only supported for remote challenges.".format(challenge.title)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if not challenge.allow_resuming_submissions:
        response_data = {
            "error": "Challenge {} does not allow resuming submissions.".format(challenge.title)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    message = handle_submission_resume(submission, Submission.RESUMING)
    publish_submission_message(message)
    response_data = {
        "success": "Submission is successfully resumed"
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_submissions_for_challenge(request, challenge_pk):

    challenge = get_challenge_model(challenge_pk)

    if not is_user_a_staff(request.user) and not is_user_a_host_of_challenge(request.user, challenge.id):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    submission_status = request.query_params.get("status", None)

    valid_submission_status = [
        Submission.SUBMITTED,
        Submission.RUNNING,
        Submission.QUEUED,
        Submission.RESUMING,
        Submission.FAILED,
        Submission.CANCELLED,
        Submission.FINISHED,
        Submission.SUBMITTING,
    ]

    if submission_status not in valid_submission_status:
        response_data = {
            "error": "Invalid submission status {}".format(submission_status)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    submissions_done_in_challenge = Submission.objects.filter(
        challenge_phase__challenge=challenge.id, status=submission_status
    )

    serializer = SubmissionSerializer(
        submissions_done_in_challenge, many=True, context={"request": request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    methods=["get"],
    manual_parameters=[
        openapi.Parameter(
            name="queue_name",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Queue Name",
            required=True,
        )
    ],
    operation_id="get_submission_message_from_queue",
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "body": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="SQS message queue dict object",
                        properties={
                            "challenge_pk": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Primary key for the challenge in the database",
                            ),
                            "phase_pk": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Primary key for the challenge phase in the database",
                            ),
                            "submission_pk": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Primary key for the submission in the database",
                            ),
                            "submitted_image_uri": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="The AWS ECR URL for the pushed docker image in docker based challenges",
                            ),
                        },
                    ),
                    "receipt_handle": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="SQS message receipt handle",
                    ),
                },
            ),
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_submission_message_from_queue(request, queue_name):
    """
    API to fetch submission message from AWS SQS queue.

    - Arguments:
        ``queue_name``: AWS SQS queue name

    - Returns:
        ``body``: The message body content as a key-value pair
        ``receipt_handle``: The message receipt handle
    """
    try:
        challenge = Challenge.objects.get(queue=queue_name)  # noqa
    except Challenge.DoesNotExist:
        response_data = {
            "error": "Challenge with queue name {} does not exist".format(
                queue_name
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to access this resource"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    queue = get_or_create_sqs_queue(queue_name, challenge)
    try:
        messages = queue.receive_messages()
        if len(messages):
            message_receipt_handle = messages[0].receipt_handle
            message_body = json.loads(messages[0].body)
            logger.info(
                "A submission is received with pk {}".format(
                    message_body.get("submission_pk")
                )
            )
        else:
            logger.info("No submission received")
            message_receipt_handle = None
            message_body = None

        response_data = {
            "body": message_body,
            "receipt_handle": message_receipt_handle,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except botocore.exceptions.ClientError as ex:
        response_data = {"error": ex}
        logger.exception("Exception raised: {}".format(ex))
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    methods=["post"],
    manual_parameters=[
        openapi.Parameter(
            name="queue_name",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description="Queue Name",
            required=True,
        )
    ],
    operation_id="delete_submission_message_from_queue",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "receipt_handle": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Receipt handle for the message to be deleted",
            )
        },
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            "{'success': 'Message deleted successfully from the queue <queue-name>'}"
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "{'error': 'Error message goes here'}"
        ),
    },
)
@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def delete_submission_message_from_queue(request, queue_name):
    """
    API to delete submission message from AWS SQS queue

    - Arguments:
        ``queue_name``  -- The unique authentication token provided by challenge hosts

    - Request Body:
        ``receipt_handle`` -- The receipt handle of the message to be deleted
    """
    try:
        challenge = Challenge.objects.get(queue=queue_name)
    except Challenge.DoesNotExist:
        response_data = {
            "error": "Challenge with queue name {} does not exists".format(
                queue_name
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge_pk = challenge.pk
    receipt_handle = request.data["receipt_handle"]
    if not receipt_handle:
        response_data = {
            "error": "Please add message receipt handle in the body"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized to access this resource"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    queue = get_or_create_sqs_queue(queue_name, challenge)
    try:
        message = queue.Message(receipt_handle)
        message.delete()
        response_data = {
            "success": "Message deleted successfully from the queue: {}".format(
                queue_name
            )
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except botocore.exceptions.ClientError as ex:
        response_data = {"error": ex}
        logger.exception(
            "SQS message is not deleted due to {}".format(response_data)
        )
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_signed_url_for_submission_related_file(request):
    """Returns S3 signed URL for a particular file residing on S3 bucket

    Arguments:
        request {object} -- Request object

    Returns:
        Response object -- Response object with appropriate response code (200/400/403/404)
    """

    # Assumption: file will be stored in this format: 'team_{id}/submission_{id}/.../file.log'
    bucket = request.query_params.get("bucket", None)
    key = request.query_params.get("key", None)

    if not bucket or not key:
        response_data = {"error": "key and bucket names can't be empty"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        splits = key.split("/")
        participant_team_id, submission_id = (
            splits[0].replace("team_", ""),
            splits[1].replace("submission_", ""),
        )
    except Exception:
        response_data = {
            "error": "Invalid file path format. Please try again with correct file path format."
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    participant_team = get_participant_team_model(participant_team_id)
    submission = get_submission_model(submission_id)
    challenge_pk = submission.challenge_phase.challenge.pk

    if submission.participant_team != participant_team:
        response_data = {
            "error": "You are not authorized to access this file."
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    if is_user_part_of_participant_team(
        request.user, participant_team
    ) or is_user_a_host_of_challenge(request.user, challenge_pk):
        aws_keys = get_aws_credentials_for_challenge(challenge_pk)
        s3 = get_boto3_client("s3", aws_keys)
        url = s3.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": bucket, "Key": key}
        )
        response_data = {"signed_url": url}
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "error": "You are not authorized to access this file."
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)


@api_view(["PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_leaderboard_data(request, leaderboard_data_pk):
    """API endpoint to update a metric in leaderboard data

    Arguments:
        request {HttpRequest} -- The request object
        leaderboard_data_pk {int} -- Primary key from leaderboard data table
    """

    try:
        leaderboard_data = LeaderboardData.objects.get(
            Q(is_disabled=False) | Q(is_disabled__isnull=True),
            pk=leaderboard_data_pk
        )
    except LeaderboardData.DoesNotExist:
        response_data = {"error": "Leaderboard data does not exist"}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    challenge = (
        leaderboard_data.challenge_phase_split.challenge_phase.challenge
    )

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.get("leaderboard_data")
    if data is None:
        response_data = {"error": "leaderboard_data can't be blank"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = json.loads(data)
    except (ValueError, TypeError) as exc:
        response_data = {
            "error": "`leaderboard_data` key contains invalid data with error {}."
            "Please try again with correct format.".format(str(exc))
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    leaderboard_metrics = leaderboard_data.leaderboard.schema.get("labels")
    missing_metrics = []
    extra_metrics = []
    malformed_metrics = []
    for metric in leaderboard_metrics:
        if metric not in data:
            missing_metrics.append(metric)

    for metric, value in data.items():
        if metric not in leaderboard_metrics:
            extra_metrics.append(metric)

        if not (isinstance(value, float) or isinstance(value, int)):
            malformed_metrics.append((metric, type(value)))

    if len(missing_metrics) and len(extra_metrics):
        response_data = {
            "error": "Following metrics {0} are missing and following metrics are invalid {1} in the "
            "leaderboard data".format(missing_metrics, extra_metrics)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if len(missing_metrics):
        response_data = {
            "error": "Following metrics are missing in the "
            "leaderboard data: {}".format(missing_metrics)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if len(extra_metrics):
        response_data = {
            "error": "Following metrics are invalid in the "
            "leaderboard data: {}".format(extra_metrics)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if len(malformed_metrics):
        response_data = {
            "error": "Values for following metrics are not of"
            "float/int: {}".format(malformed_metrics)
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    result = {"result": data}
    serializer = LeaderboardDataSerializer(
        leaderboard_data,
        data=result,
        partial=True,
        context={"request": request},
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_bearer_token(request, challenge_pk):
    """API to generate and return bearer token AWS EKS requests

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {int} -- The challenge pk for which bearer token is to be generated

    Returns:
        Response object -- Response object with appropriate response code (200/400/404)
    """
    challenge = get_challenge_model(challenge_pk)

    if not is_user_a_host_of_challenge(request.user, challenge.id):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not challenge.is_docker_based:
        response_data = {
            "error": "The challenge doesn't require uploading Docker images, hence there isn't a need for bearer token."
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

    cluster_name = challenge_evaluation_cluster.name
    bearer_token = generate_aws_eks_bearer_token(cluster_name, challenge)
    response_data = {
        "aws_eks_bearer_token": bearer_token,
        "cluster_name": cluster_name,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_github_badge_data(
    request, challenge_phase_split_pk, participant_team_pk
):
    """
    Add API to get data for dynamically generating github badges
    Ref: https://shields.io/endpoint
    Arguments:
        request {HttpRequest} -- The request object
        phase_pk {[int]} -- Challenge phase primary key
        participant_team_pk {[int]} -- Participant team primary key

    Returns:
        {dict} -- A dict which contains keys schemaVersion, label, message and color of badge
    """
    challenge_phase_split = get_challenge_phase_split_model(
        challenge_phase_split_pk
    )
    challenge_obj = challenge_phase_split.challenge_phase.challenge
    data = {"schemaVersion": 1, "label": "EvalAI", "color": "blue"}

    (
        response_data,
        http_status_code,
    ) = calculate_distinct_sorted_leaderboard_data(
        request.user,
        challenge_obj,
        challenge_phase_split,
        only_public_entries=True,
        order_by=None,
    )
    if http_status_code == status.HTTP_400_BAD_REQUEST:
        return Response(response_data, status=http_status_code)

    for idx, team_data in enumerate(response_data):
        if team_data["submission__participant_team"] == int(
            participant_team_pk
        ):
            data["message"] = "{} Rank #{}".format(
                challenge_obj.title, idx + 1
            )
            break
        else:
            data["message"] = challenge_obj.title
    return Response(data, status=http_status_code)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def challenge_phase_submission_count_by_status(request, challenge_phase_pk):
    """
    API for fetching count of submissions by status for a challenge phase

    Arguments:
        request {HttpRequest} -- request object
        challenge_phase_pk {int} -- challenge phase pk

    Returns:
        Response object -- Response object with appropriate response code (200/400/404)
    """
    # check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    challenge = challenge_phase.challenge

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Sorry, you are not authorized to make this request"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    submissions = (
        Submission.objects.filter(challenge_phase=challenge_phase)
        .values("status")
        .annotate(count=Count("id"))
    )

    response_data = {"status": submissions}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_submission_file_presigned_url(request, challenge_phase_pk):
    """
    API to generate a presigned url to upload a submission file

    Arguments:
        request {HttpRequest} -- The request object
        challenge_phase_pk {int} -- Challenge phase primary key
    Returns:
         Response Object -- An object containing the presignd url and submission id, or an error message if some failure occurs
    """
    if settings.DEBUG:
        response_data = {
            "error": "Sorry, this feature is not available in development or test environment."
        }
        return Response(response_data)

    # Check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    challenge = challenge_phase.challenge

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )

    if not challenge.is_active:
        response_data = {"error": "Challenge is not active"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check if challenge phase is active
    if not challenge_phase.is_active:
        response_data = {
            "error": "Sorry, cannot accept submissions since challenge phase is not active"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check if user is a challenge host or a participant
    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        # Check if challenge phase is public and accepting solutions
        if not challenge_phase.is_public:
            response_data = {
                "error": "Sorry, cannot accept submissions since challenge phase is not public"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        if not challenge.approved_by_admin:
            response_data = {
                "error": "Challenge is not yet approved by admin."
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        # if allowed email ids list exist, check if the user exist in that list or not
        if challenge_phase.allowed_email_ids:
            if request.user.email not in challenge_phase.allowed_email_ids:
                response_data = {
                    "error": "Sorry, you are not allowed to participate in this challenge phase"
                }
                return Response(
                    response_data, status=status.HTTP_403_FORBIDDEN
                )

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_id)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "You haven't participated in the challenge"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    all_participants_email = participant_team.get_all_participants_email()
    for participant_email in all_participants_email:
        if participant_email in challenge.banned_email_ids:
            message = "You're a part of {} team and it has been banned from this challenge. \
            Please contact the challenge host.".format(
                participant_team.team_name
            )
            response_data = {"error": message}
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    # Fetch the number of submissions under progress.
    submissions_in_progress_status = [
        Submission.SUBMITTED,
        Submission.SUBMITTING,
        Submission.RESUMING,
        Submission.QUEUED,
        Submission.RUNNING,
    ]
    submissions_in_progress = Submission.objects.filter(
        participant_team=participant_team_id,
        challenge_phase=challenge_phase,
        status__in=submissions_in_progress_status,
    ).count()

    if (
        submissions_in_progress
        >= challenge_phase.max_concurrent_submissions_allowed
    ):
        message = "You have {} submissions that are being processed. \
                   Please wait for them to finish and then try again."
        response_data = {"error": message.format(submissions_in_progress)}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    file_ext = os.path.splitext(request.data["file_name"])[-1]
    random_file_name = uuid.uuid4()
    # This file shall be replaced with the one uploaded through the presigned url from the CLI
    input_file = SimpleUploadedFile(
        "{}{}".format(random_file_name, file_ext),
        b"file_content",
        content_type="text/plain",
    )
    submission_data = request.data.copy()

    if submission_data.get("is_public") is None:
        submission_data["is_public"] = (
            True if challenge_phase.is_submission_public else False
        )
    else:
        submission_data["is_public"] = json.loads(request.data["is_public"])

    # Override submission visibility if leaderboard_public = False for a challenge phase
    if not challenge_phase.leaderboard_public:
        submission_data["is_public"] = challenge_phase.is_submission_public

    submission_data["input_file"] = input_file
    serializer = SubmissionSerializer(
        data=submission_data,
        context={
            "participant_team": participant_team,
            "challenge_phase": challenge_phase,
            "request": request,
        },
    )
    # Set default num of chunks to 1 if num of chunks is not specified
    num_file_chunks = 1
    if request.data.get("num_file_chunks"):
        num_file_chunks = int(request.data["num_file_chunks"])

    response = {}
    if serializer.is_valid():
        serializer.save()
        submission = serializer.instance

        file_key_on_s3 = "{}/{}".format(
            settings.MEDIAFILES_LOCATION, submission.input_file.name
        )
        response = generate_presigned_url_for_multipart_upload(
            file_key_on_s3, challenge.pk, num_file_chunks
        )
        if response.get("error"):
            response_data = response
            response = Response(
                response_data, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            response_data = {
                "presigned_urls": response.get("presigned_urls"),
                "upload_id": response.get("upload_id"),
                "submission_pk": submission.pk,
            }
            response = Response(response_data, status=status.HTTP_201_CREATED)
        return response
    response_data = {"error": serializer.errors}
    return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def finish_submission_file_upload(request, challenge_phase_pk, submission_pk):
    """
    API to complete multipart upload of presigned url submission

    Arguments:
        request {HttpRequest} -- The request object
        challenge_phase_pk {int} -- Challenge phase primary key
        submission_pk {int} -- Submission primary key
    Returns:
         Response Object -- An object containing the presignd url and submission id, or an error message if some failure occurs
    """
    if settings.DEBUG:
        response_data = {
            "error": "Sorry, this feature is not available in development or test environment."
        }
        return Response(response_data)

    # Check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    challenge = challenge_phase.challenge

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )

    if not challenge.is_active:
        response_data = {"error": "Challenge is not active"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check if challenge phase is active
    if not challenge_phase.is_active:
        response_data = {
            "error": "Sorry, cannot accept submissions since challenge phase is not active"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check if user is a challenge host or a participant
    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        # Check if challenge phase is public and accepting solutions
        if not challenge_phase.is_public:
            response_data = {
                "error": "Sorry, cannot accept submissions since challenge phase is not public"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        if not challenge.approved_by_admin:
            response_data = {
                "error": "Challenge is not yet approved by admin."
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        # if allowed email ids list exist, check if the user exist in that list or not
        if challenge_phase.allowed_email_ids:
            if request.user.email not in challenge_phase.allowed_email_ids:
                response_data = {
                    "error": "Sorry, you are not allowed to participate in this challenge phase"
                }
                return Response(
                    response_data, status=status.HTTP_403_FORBIDDEN
                )

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_id)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "You haven't participated in the challenge"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    all_participants_email = participant_team.get_all_participants_email()
    for participant_email in all_participants_email:
        if participant_email in challenge.banned_email_ids:
            message = "You're a part of {} team and it has been banned from this challenge. \
            Please contact the challenge host.".format(
                participant_team.team_name
            )
            response_data = {"error": message}
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    if request.data.get("parts") is None:
        response_data = {"error": "Uploaded file Parts metadata is missing"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("upload_id") is None:
        response_data = {"error": "Uploaded file UploadId is missing"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    file_parts = json.loads(request.data["parts"])
    upload_id = request.data["upload_id"]
    response = {}
    try:
        submission = get_submission_model(submission_pk)
        file_key_on_s3 = "{}/{}".format(
            settings.MEDIAFILES_LOCATION, submission.input_file.name
        )
        data = complete_s3_multipart_file_upload(
            file_parts, upload_id, file_key_on_s3, challenge.pk
        )
        if data.get("error"):
            response_data = data
            response = Response(
                response_data, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            response_data = {
                "upload_id": upload_id,
                "submission_pk": submission.pk,
            }
            response = Response(response_data, status=status.HTTP_201_CREATED)
    except Submission.DoesNotExist:
        response_data = {"error": "Submission does not exist"}
        response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    return response


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def send_submission_message(request, challenge_phase_pk, submission_pk):
    """
    API to send a submisison message to the challenge specific SQS queue

    Arguments:
        request {HttpRequest} -- The request object
        challenge_phase_pk {int} -- Challenge phase primary key
        submission_pk {int} -- Submission primary key
    Returns:
         Response Object -- An object containing an empty dict and having a HTTP_200_0k status
    """
    try:
        challenge_phase = get_challenge_phase_model(challenge_phase_pk)
    except ChallengePhase.DoesNotExist:
        response_data = {"error": "Challenge Phase does not exist"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    challenge = challenge_phase.challenge

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )

    if not challenge.is_active:
        response_data = {"error": "Challenge is not active"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if not challenge_phase.is_active:
        response_data = {
            "error": "Sorry, cannot accept submissions since challenge phase is not active"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        if not challenge_phase.is_public:
            response_data = {
                "error": "Sorry, cannot accept submissions since challenge phase is not public"
            }
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        if not challenge.approved_by_admin:
            response_data = {
                "error": "Challenge is not yet approved by admin."
            }
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )

        if challenge_phase.allowed_email_ids:
            if request.user.email not in challenge_phase.allowed_email_ids:
                response_data = {
                    "error": "Sorry, you are not allowed to participate in this challenge phase"
                }
                return Response(
                    response_data, status=status.HTTP_403_FORBIDDEN
                )

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge.pk
    )
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_id)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "You haven't participated in the challenge"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    all_participants_email = participant_team.get_all_participants_email()
    for participant_email in all_participants_email:
        if participant_email in challenge.banned_email_ids:
            message = "You're a part of {} team and it has been banned from this challenge. \
            Please contact the challenge host.".format(
                participant_team.team_name
            )
            response_data = {"error": message}
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        get_submission_model(submission_pk)
    except Submission.DoesNotExist:
        response_data = {"error": "Submission does not exist"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    submission_message = {
        "submission_pk": submission_pk,
        "phase_pk": challenge_phase_pk,
        "challenge_pk": challenge.pk,
    }

    publish_submission_message(submission_message)
    response_data = {}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_submission_started_at(request, submission_pk):
    """
    API Endpoint for updating the submission evaluation start time.
    """
    try:
        submission = Submission.objects.get(
            id=submission_pk,
        )
    except Submission.DoesNotExist:
        response_data = {"error": "Submission does not exist"}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    serializer = SubmissionSerializer(
        submission,
        data={"started_at": str(timezone.now())},
        context={"request": request},
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def update_submission_meta(request, challenge_pk, submission_pk):
    """
    Common API Endpoint for updating the submission meta data for hosts and participants.
    """

    if is_user_a_host_of_challenge(request.user, challenge_pk):
        submission = get_submission_model(submission_pk)

        serializer = SubmissionSerializer(
            submission,
            data=request.data,
            context={
                "request": request,
            },
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
    else:
        participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_pk
        )

        participant_team = get_participant_model(participant_team_pk)

        try:
            submission = Submission.objects.get(
                id=submission_pk,
                participant_team=participant_team,
            )
        except Submission.DoesNotExist:
            response_data = {
                "error": "Submission {} does not exist".format(submission_pk)
            }
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        serializer = SubmissionSerializer(
            submission,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
