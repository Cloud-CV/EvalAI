import datetime

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)

from django.db.models.expressions import RawSQL
from django.db.models import FloatField
from django.utils import timezone

from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from accounts.permissions import HasVerifiedEmail
from base.utils import paginated_queryset, StandardResultSetPagination
from challenges.models import (
    ChallengePhase,
    Challenge,
    ChallengePhaseSplit,
    LeaderboardData,)
from challenges.utils import get_challenge_model, get_challenge_phase_model
from participants.models import (ParticipantTeam,)
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge,)

from .models import Submission
from .sender import publish_submission_message
from .serializers import SubmissionSerializer


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_submission(request, challenge_id, challenge_phase_id):
    """API Endpoint for making a submission to a challenge"""

    # check if the challenge exists or not
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # check if the challenge phase exists or not
    try:
        challenge_phase = ChallengePhase.objects.get(
            pk=challenge_phase_id, challenge=challenge)
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'Challenge Phase does not exist'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        # getting participant team object for the user for a particular challenge.
        participant_team_id = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_id)

        # check if participant team exists or not.
        try:
            ParticipantTeam.objects.get(pk=participant_team_id)
        except ParticipantTeam.DoesNotExist:
            response_data = {'error': 'You haven\'t participated in the challenge'}
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        submission = Submission.objects.filter(participant_team=participant_team_id,
                                               challenge_phase=challenge_phase).order_by('-submitted_at')
        paginator, result_page = paginated_queryset(submission, request)
        try:
            serializer = SubmissionSerializer(result_page, many=True, context={'request': request})
            response_data = serializer.data
            return paginator.get_paginated_response(response_data)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':

        # check if the challenge is active or not
        if not challenge.is_active:
            response_data = {'error': 'Challenge is not active'}
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

        # check if challenge phase is active
        if not challenge_phase.is_active:
            response_data = {
                'error': 'Sorry, cannot accept submissions since challenge phase is not active'}
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

        # check if challenge phase is public and accepting solutions
        if not challenge_phase.is_public:
            response_data = {
                'error': 'Sorry, cannot accept submissions since challenge phase is not public'}
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

        participant_team_id = get_participant_team_id_of_user_for_a_challenge(
            request.user, challenge_id)
        try:
            participant_team = ParticipantTeam.objects.get(pk=participant_team_id)
        except ParticipantTeam.DoesNotExist:
            response_data = {'error': 'You haven\'t participated in the challenge'}
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmissionSerializer(data=request.data,
                                          context={'participant_team': participant_team,
                                                   'challenge_phase': challenge_phase,
                                                   'request': request
                                                   })
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            submission = serializer.instance
            # publish message in the queue
            publish_submission_message(challenge_id, challenge_phase_id, submission.id)
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['PATCH'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def change_submission_data_and_visibility(request, challenge_pk, challenge_phase_pk, submission_pk):
    """
    API Endpoint for updating the submission meta data
    and changing submission visibility.
    """

    # check if the challenge exists or not
    challenge = get_challenge_model(challenge_pk)

    # check if the challenge phase exists or not
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    if not challenge.is_active:
        response_data = {'error': 'Challenge is not active'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # check if challenge phase is public and accepting solutions
    if not challenge_phase.is_public:
        response_data = {
            'error': 'Sorry, cannot accept submissions since challenge phase is not public'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge_pk)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'You haven\'t participated in the challenge'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = Submission.objects.get(participant_team=participant_team,
                                            challenge_phase=challenge_phase,
                                            id=submission_pk)
    except Submission.DoesNotExist:
        response_data = {'error': 'Submission does not exist'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        is_public = request.data['is_public']
        if is_public is True:
            when_made_public = datetime.datetime.now()
            request.data['when_made_public'] = when_made_public
    except KeyError:
        pass

    serializer = SubmissionSerializer(submission,
                                      data=request.data,
                                      context={
                                               'participant_team': participant_team,
                                               'challenge_phase': challenge_phase,
                                               'request': request
                                      },
                                      partial=True)

    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([AnonRateThrottle])
@api_view(['GET'])
def leaderboard(request, challenge_phase_split_id):
    """Returns leaderboard for a corresponding Challenge Phase Split"""

    # check if the challenge exists or not
    try:
        challenge_phase_split = ChallengePhaseSplit.objects.get(
            pk=challenge_phase_split_id)
    except ChallengePhaseSplit.DoesNotExist:
        response_data = {'error': 'Challenge Phase Split does not exist'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Check if the Challenge Phase Split is publicly visible or not
    if challenge_phase_split.visibility != ChallengePhaseSplit.PUBLIC:
        response_data = {'error': 'Sorry, leaderboard is not public yet for this Challenge Phase Split!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Get the leaderboard associated with the Challenge Phase Split
    leaderboard = challenge_phase_split.leaderboard

    # Get the default order by key to rank the entries on the leaderboard
    try:
        default_order_by = leaderboard.schema['default_order_by']
    except:
        response_data = {'error': 'Sorry, Default filtering key not found in leaderboard schema!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Get all the successful submissions related to the challenge phase split
    leaderboard_data = LeaderboardData.objects.filter(
        challenge_phase_split=challenge_phase_split,
        submission__is_public=True,
        submission__is_flagged=False).order_by('created_at')
    leaderboard_data = leaderboard_data.annotate(
        filtering_score=RawSQL('result->>%s', (default_order_by, ), output_field=FloatField())).values(
            'id', 'submission__participant_team__team_name',
            'challenge_phase_split', 'result', 'filtering_score', 'leaderboard__schema')

    sorted_leaderboard_data = sorted(leaderboard_data, key=lambda k: float(k['filtering_score']), reverse=True)

    distinct_sorted_leaderboard_data = []
    team_list = []

    for data in sorted_leaderboard_data:
        if data['submission__participant_team__team_name'] in team_list:
            continue
        else:
            distinct_sorted_leaderboard_data.append(data)
            team_list.append(data['submission__participant_team__team_name'])

    leaderboard_labels = challenge_phase_split.leaderboard.schema['labels']
    for item in distinct_sorted_leaderboard_data:
        item['result'] = [item['result'][index.lower()] for index in leaderboard_labels]

    paginator, result_page = paginated_queryset(
                                                distinct_sorted_leaderboard_data,
                                                request,
                                                pagination_class=StandardResultSetPagination())
    response_data = result_page
    return paginator.get_paginated_response(response_data)


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_remaining_submissions(request, challenge_phase_pk, challenge_pk):

    get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge_pk)

    # Conditional check for the existence of participant team of the user.
    if not participant_team_pk:
        response_data = {'error': 'You haven\'t participated in the challenge'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    max_submission_per_day = challenge_phase.max_submissions_per_day

    max_submission = challenge_phase.max_submissions

    submissions_done_today_count = Submission.objects.filter(
        challenge_phase__challenge=challenge_pk,
        challenge_phase=challenge_phase_pk,
        participant_team=participant_team_pk,
        submitted_at__gte=timezone.now().date()).count()

    failed_submissions_count = Submission.objects.filter(
        challenge_phase__challenge=challenge_pk,
        challenge_phase=challenge_phase_pk,
        participant_team=participant_team_pk,
        status=Submission.FAILED,
        submitted_at__gte=timezone.now().date()).count()

    # Checks if today's successfull submission is greater than or equal to max submission per day.
    if ((submissions_done_today_count - failed_submissions_count) >= max_submission_per_day
            or (max_submission_per_day == 0)):
        # Get the UTC time of the instant when the above condition is true.
        date_time_now = timezone.now()
        # Calculate the next day's date.
        date_time_tomorrow = date_time_now.date() + datetime.timedelta(1)
        utc = timezone.utc
        # Get the midnight time of the day i.e. 12:00 AM of next day.
        midnight = utc.localize(datetime.datetime.combine(
            date_time_tomorrow, datetime.time()))
        # Subtract the current time from the midnight time to get the remaining time for the next day's submissions.
        remaining_time = midnight - date_time_now
        # Return the remaining time with a message.
        response_data = {'message': 'You have exhausted today\'s submission limit',
                         'remaining_time': remaining_time
                         }
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        # Calculate the remaining submissions for today.
        remaining_submissions_today_count = (max_submission_per_day -
                                             (submissions_done_today_count -
                                              failed_submissions_count)
                                             )
        # calculate the remaining submissions from total submissions.
        remaining_submission_count = max_submission - \
            (submissions_done_today_count - failed_submissions_count)
        # Return the above calculated data.
        response_data = {'remaining_submissions_today_count': remaining_submissions_today_count,
                         'remaining_submissions': remaining_submission_count
                         }
        return Response(response_data, status=status.HTTP_200_OK)
