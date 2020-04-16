import botocore
import datetime
import json
import logging

import requests
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)

from django.core.files.base import ContentFile
from django.db import transaction, IntegrityError
from django.db.models.expressions import RawSQL
from django.db.models import FloatField, Q
from django.utils import timezone

from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from accounts.permissions import HasVerifiedEmail
from base.utils import (
    paginated_queryset,
    StandardResultSetPagination,
    get_or_create_sqs_queue_object,
    get_boto3_client,
)
from challenges.models import (
    ChallengePhase,
    Challenge,
    ChallengeEvaluationCluster,
    ChallengePhaseSplit,
    LeaderboardData,
)
from challenges.utils import (
    get_challenge_model,
    get_challenge_phase_model,
    get_aws_credentials_for_challenge,
)
from hosts.models import ChallengeHost
from hosts.utils import is_user_a_host_of_challenge
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
    get_submission_model,
    get_remaining_submission_for_a_phase,
    is_url_valid,
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
@authentication_classes((ExpiringTokenAuthentication,))
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
        ).order_by("-submitted_at")
        filtered_submissions = SubmissionFilter(
            request.GET, queryset=submission
        )
        paginator, result_page = paginated_queryset(
            filtered_submissions.qs, request
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
        }
        if challenge.is_docker_based:
            try:
                file_content = json.loads(request.FILES["input_file"].read())
                message["submitted_image_uri"] = file_content[
                    "submitted_image_uri"
                ]
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
@authentication_classes((ExpiringTokenAuthentication,))
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
@throttle_classes([AnonRateThrottle])
def leaderboard(request, challenge_phase_split_id):
    """
    Returns leaderboard for a corresponding Challenge Phase Split

    - Arguments:
        ``challenge_phase_split_id``: Primary key for the challenge phase split for which leaderboard is to be fetched

    - Returns:
        Leaderboard entry objects in a list
    """

    # check if the challenge exists or not
    try:
        challenge_phase_split = ChallengePhaseSplit.objects.get(
            pk=challenge_phase_split_id
        )
    except ChallengePhaseSplit.DoesNotExist:
        response_data = {"error": "Challenge Phase Split does not exist"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Get the leaderboard associated with the Challenge Phase Split
    leaderboard = challenge_phase_split.leaderboard

    # Get the default order by key to rank the entries on the leaderboard
    try:
        default_order_by = leaderboard.schema["default_order_by"]
    except KeyError:
        response_data = {
            "error": "Sorry, Default filtering key not found in leaderboard schema!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Exclude the submissions done by members of the host team
    # while populating leaderboard
    challenge_obj = challenge_phase_split.challenge_phase.challenge
    challenge_hosts_emails = (
        challenge_obj.creator.get_all_challenge_host_email()
    )
    is_challenge_phase_public = challenge_phase_split.challenge_phase.is_public
    # Exclude the submissions from challenge host team to be displayed on the leaderboard of public phases
    challenge_hosts_emails = (
        [] if not is_challenge_phase_public else challenge_hosts_emails
    )

    challenge_host_user = is_user_a_host_of_challenge(
        request.user, challenge_obj.pk
    )

    all_banned_email_ids = challenge_obj.banned_email_ids

    # Check if challenge phase leaderboard is public for participant user or not
    if (
        challenge_phase_split.visibility != ChallengePhaseSplit.PUBLIC
        and not challenge_host_user
    ):
        response_data = {"error": "Sorry, the leaderboard is not public!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    leaderboard_data = LeaderboardData.objects.exclude(
        Q(submission__created_by__email__in=challenge_hosts_emails)
        & Q(submission__is_baseline=False)
    )

    # Get all the successful submissions related to the challenge phase split
    leaderboard_data = leaderboard_data.filter(
        challenge_phase_split=challenge_phase_split,
        submission__is_flagged=False,
        submission__status=Submission.FINISHED,
    ).order_by("-created_at")

    leaderboard_data = leaderboard_data.annotate(
        filtering_score=RawSQL(
            "result->>%s", (default_order_by,), output_field=FloatField()
        ),
        filtering_error=RawSQL(
            "error->>%s",
            ("error_{0}".format(default_order_by),),
            output_field=FloatField(),
        ),
    ).values(
        "id",
        "submission__participant_team",
        "submission__participant_team__team_name",
        "submission__participant_team__team_url",
        "submission__is_baseline",
        "challenge_phase_split",
        "result",
        "error",
        "filtering_score",
        "filtering_error",
        "leaderboard__schema",
        "submission__submitted_at",
        "submission__method_name",
    )

    if challenge_phase_split.visibility == ChallengePhaseSplit.PUBLIC:
        leaderboard_data = leaderboard_data.filter(submission__is_public=True)

    all_banned_participant_team = []
    for leaderboard_item in leaderboard_data:
        participant_team_id = leaderboard_item["submission__participant_team"]
        participant_team = ParticipantTeam.objects.get(id=participant_team_id)
        all_participants_email_ids = (
            participant_team.get_all_participants_email()
        )
        for participant_email in all_participants_email_ids:
            if participant_email in all_banned_email_ids:
                all_banned_participant_team.append(participant_team_id)
                break
        if leaderboard_item["error"] is None:
            leaderboard_item.update(filtering_error=0)

    if challenge_phase_split.show_leaderboard_by_latest_submission:
        sorted_leaderboard_data = leaderboard_data
    else:
        sorted_leaderboard_data = sorted(
            leaderboard_data,
            key=lambda k: (
                float(k["filtering_score"]),
                float(-k["filtering_error"]),
            ),
            reverse=True
            if challenge_phase_split.is_leaderboard_order_descending
            else False,
        )

    distinct_sorted_leaderboard_data = []
    team_list = []
    for data in sorted_leaderboard_data:
        if (
            data["submission__participant_team__team_name"] in team_list
            or data["submission__participant_team"]
            in all_banned_participant_team
        ):
            continue
        elif data["submission__is_baseline"] is True:
            distinct_sorted_leaderboard_data.append(data)
        else:
            distinct_sorted_leaderboard_data.append(data)
            team_list.append(data["submission__participant_team__team_name"])

    leaderboard_labels = challenge_phase_split.leaderboard.schema["labels"]
    for item in distinct_sorted_leaderboard_data:
        item["result"] = [
            item["result"][index] for index in leaderboard_labels
        ]
        if item["error"] is not None:
            item["error"] = [
                item["error"]["error_{0}".format(index)]
                for index in leaderboard_labels
            ]

    paginator, result_page = paginated_queryset(
        distinct_sorted_leaderboard_data,
        request,
        pagination_class=StandardResultSetPagination(),
    )
    response_data = result_page
    return paginator.get_paginated_response(response_data)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
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
        remaining_submission_message, response_status = get_remaining_submission_for_a_phase(
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


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
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
        serializer = SubmissionSerializer(
            submission, context={"request": request}
        )
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

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
@authentication_classes((ExpiringTokenAuthentication,))
def update_submission(request, challenge_pk):
    """
    API endpoint to update submission related attributes

    Query Parameters:

     - ``challenge_phase``: challenge phase id, e.g. 123 (**required**)
     - ``submission``: submission id, e.g. 123 (**required**)
     - ``stdout``: Stdout after evaluation, e.g. "Evaluation completed in 2 minutes" (**required**)
     - ``stderr``: Stderr after evaluation, e.g. "Failed due to incorrect file format" (**required**)
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

                leaderboard_metrics = challenge_phase_split.leaderboard.schema.get(
                    "labels"
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

                data = {"result": accuracies}
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
        if submission_status not in [Submission.RUNNING]:
            response_data = {"error": "Sorry, submission status is invalid"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "status": submission_status,
            "started_at": timezone.now(),
            "job_name": jobs,
        }
        serializer = SubmissionSerializer(
            submission, data=data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def re_run_submission(request, submission_pk):
    """
    API endpoint to re-run a submission.
    Only challenge host has access to this endpoint.
    """
    try:
        submission = Submission.objects.get(pk=submission_pk)
    except Submission.DoesNotExist:
        response_data = {
            "error": "Submission {} does not exist".format(submission_pk)
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    # get the challenge and challenge phase object
    challenge_phase = submission.challenge_phase
    challenge = challenge_phase.challenge

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "Only challenge hosts are allowed to re-run a submission"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    if not challenge.is_active:
        response_data = {
            "error": "Challenge {} is not active".format(challenge.title)
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    message = {
        "challenge_pk": challenge.pk,
        "phase_pk": challenge_phase.pk,
        "submission_pk": submission.pk,
    }

    if submission.challenge_phase.challenge.is_docker_based:
        try:
            response = requests.get(submission.input_file)
        except Exception as e:
            response_data = {
                "error": "Failed to get submission input file with error: {0}".format(
                    e
                )
            }
            return Response(
                response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if response and response.status_code == 200:
            message["submitted_image_uri"] = response.json()[
                "submitted_image_uri"
            ]

    publish_submission_message(message)
    response_data = {
        "success": "Submission is successfully submitted for re-running"
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_submissions_for_challenge(request, challenge_pk):

    challenge = get_challenge_model(challenge_pk)

    if not is_user_a_host_of_challenge(request.user, challenge.id):
        response_data = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    submission_status = request.query_params.get("status", None)

    valid_submission_status = [
        Submission.SUBMITTED,
        Submission.RUNNING,
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
@authentication_classes((ExpiringTokenAuthentication,))
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

    queue = get_or_create_sqs_queue_object(queue_name)
    try:
        messages = queue.receive_messages()
        if len(messages):
            message_receipt_handle = messages[0].receipt_handle
            message_body = eval(messages[0].body)
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
@authentication_classes((ExpiringTokenAuthentication,))
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
    if not is_user_a_host_of_challenge(request.user, challenge_pk):
        response_data = {
            "error": "Sorry, you are not authorized to access this resource"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    queue = get_or_create_sqs_queue_object(queue_name)
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
@authentication_classes((ExpiringTokenAuthentication,))
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
@authentication_classes((ExpiringTokenAuthentication,))
def update_leaderboard_data(request, leaderboard_data_pk):
    """API endpoint to update a metric in leaderboard data

    Arguments:
        request {HttpRequest} -- The request object
        leaderboard_data_pk {int} -- Primary key from leaderboard data table
    """

    try:
        leaderboard_data = LeaderboardData.objects.get(pk=leaderboard_data_pk)
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
@authentication_classes((ExpiringTokenAuthentication,))
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
