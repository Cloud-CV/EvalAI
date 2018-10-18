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
from hosts.models import ChallengeHost
from hosts.utils import is_user_a_host_of_challenge
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

        # Fetch the number of submissions under progress.
        submissions_in_progress_status = [Submission.SUBMITTED, Submission.SUBMITTING, Submission.RUNNING]
        submissions_in_progress = Submission.objects.filter(
                                                participant_team=participant_team_id,
                                                challenge_phase=challenge_phase,
                                                status__in=submissions_in_progress_status).count()

        if submissions_in_progress >= challenge_phase.max_concurrent_submissions_allowed:
            message = 'You have {} submissions that are being processed. \
                       Please wait for them to finish and then try again.'
            response_data = {'error': message.format(submissions_in_progress)}
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

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
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


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

    # Get the leaderboard associated with the Challenge Phase Split
    leaderboard = challenge_phase_split.leaderboard

    # Get the default order by key to rank the entries on the leaderboard
    try:
        default_order_by = leaderboard.schema['default_order_by']
    except:
        response_data = {'error': 'Sorry, Default filtering key not found in leaderboard schema!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Exclude the submissions done by members of the host team
    # while populating leaderboard
    challenge_obj = challenge_phase_split.challenge_phase.challenge
    challenge_hosts_emails = challenge_obj.creator.get_all_challenge_host_email()
    leaderboard_data = LeaderboardData.objects.exclude(
        submission__created_by__email__in=challenge_hosts_emails)

    # Get all the successful submissions related to the challenge phase split
    leaderboard_data = leaderboard_data.filter(
            challenge_phase_split=challenge_phase_split,
            submission__is_public=True,
            submission__is_flagged=False,
            submission__status=Submission.FINISHED).order_by('created_at')
    leaderboard_data = leaderboard_data.annotate(
        filtering_score=RawSQL('result->>%s', (default_order_by, ), output_field=FloatField())).values(
            'id', 'submission__participant_team__team_name',
            'challenge_phase_split', 'result', 'filtering_score', 'leaderboard__schema', 'submission__submitted_at')

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
        item['result'] = [item['result'][index] for index in leaderboard_labels]

    paginator, result_page = paginated_queryset(
                                                distinct_sorted_leaderboard_data,
                                                request,
                                                pagination_class=StandardResultSetPagination())

    challenge_host_user = is_user_a_host_of_challenge(request.user, challenge_obj.pk)

    # Show the Private leaderboard only if the user is a challenge host
    if challenge_host_user:
        response_data = result_page
        return paginator.get_paginated_response(response_data)

    # Check if challenge phase leaderboard is public for participant user or not
    elif challenge_phase_split.visibility != ChallengePhaseSplit.PUBLIC:
        response_data = {'error': 'Sorry, the leaderboard is not public!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    else:
        response_data = result_page
        return paginator.get_paginated_response(response_data)


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_remaining_submissions(request, challenge_phase_pk, challenge_pk):

    '''
    Returns the number of remaining submissions that a participant can
    do per day and in total to a particular challenge phase of a
    challenge.
    '''

    # significance of get_challenge_model() here to check
    # if the challenge exists or not
    get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge_pk)

    # Conditional check for the existence of participant team of the user.
    if not participant_team_pk:
        response_data = {'error': 'You haven\'t participated in the challenge'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    max_submissions_per_day_count = challenge_phase.max_submissions_per_day

    max_submissions_count = challenge_phase.max_submissions

    submissions_done = Submission.objects.filter(
        challenge_phase__challenge=challenge_pk,
        challenge_phase=challenge_phase_pk,
        participant_team=participant_team_pk)

    failed_submissions = submissions_done.filter(
        status=Submission.FAILED)

    submissions_done_today = submissions_done.filter(
        submitted_at__gte=timezone.now().date())

    failed_submissions_done_today = submissions_done_today.filter(
        status=Submission.FAILED)

    submissions_done_count = submissions_done.count()
    failed_submissions_count = failed_submissions.count()
    submissions_done_today_count = submissions_done_today.count()
    failed_submissions_done_today_count = failed_submissions_done_today.count()

    # Checks if #today's successful submission is greater than or equal to max submission per day
    if ((submissions_done_today_count - failed_submissions_done_today_count) >= max_submissions_per_day_count
            or (max_submissions_per_day_count == 0)):
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
        remaining_submissions_today_count = (max_submissions_per_day_count -
                                             (submissions_done_today_count -
                                              failed_submissions_done_today_count)
                                             )

        # calculate the remaining submissions from total submissions.
        remaining_submission_count = max_submissions_count - \
            (submissions_done_count - failed_submissions_count)

        if remaining_submissions_today_count > remaining_submission_count:
            remaining_submissions_today_count = remaining_submission_count

        # Return the above calculated data.
        response_data = {'remaining_submissions_today_count': remaining_submissions_today_count,
                         'remaining_submissions': remaining_submission_count
                         }
        return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
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
        response_data = {'error': 'Submission {} does not exist'.format(submission_id)}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    host_team = submission.challenge_phase.challenge.creator

    if (request.user.id == submission.created_by.id
            or ChallengeHost.objects.filter(user=request.user.id, team_name__pk=host_team.pk).exists()):
        serializer = SubmissionSerializer(
            submission, context={'request': request})
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    response_data = {'error': 'Sorry, you are not authorized to access this submission.'}
    return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
