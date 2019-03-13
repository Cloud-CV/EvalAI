from datetime import timedelta

from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail

from challenges.permissions import IsChallengeCreator
from challenges.utils import get_challenge_model, get_challenge_phase_model
from jobs.models import Submission
from jobs.serializers import (LastSubmissionDateTime,
                              LastSubmissionDateTimeSerializer,
                              SubmissionCount,
                              SubmissionCountSerializer,
                              )
from participants.models import Participant
from participants.utils import get_participant_team_id_of_user_for_a_challenge
from participants.serializers import (ParticipantCount,
                                      ParticipantCountSerializer,
                                      ParticipantTeamCount,
                                      ParticipantTeamCountSerializer,
                                      )
from .serializers import (ChallengePhaseSubmissionAnalytics,
                          ChallengePhaseSubmissionAnalyticsSerializer,
                          ChallengePhaseSubmissionCount,
                          ChallengePhaseSubmissionCountSerializer,
                          LastSubmissionTimestamp,
                          LastSubmissionTimestampSerializer,
                          )


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_team_count(request, challenge_pk):
    """
        Returns the number of participant teams in a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    participant_team_count = challenge.participant_teams.count()
    participant_team_count = ParticipantTeamCount(participant_team_count)
    serializer = ParticipantTeamCountSerializer(participant_team_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_count(request, challenge_pk):
    """
        Returns the number of participants in a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    participant_teams = challenge.participant_teams.all()
    participant_count = Participant.objects.filter(team__in=participant_teams).count()
    participant_count = ParticipantCount(participant_count)
    serializer = ParticipantCountSerializer(participant_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_submission_count(request, challenge_pk, duration):
    """
        Returns submission count for a challenge according to the duration
        Valid values for duration are all, daily, weekly and monthly.
    """
    # make sure that a valid url is requested.
    if duration.lower() not in ('all', 'daily', 'weekly', 'monthly'):
        response_data = {'error': 'Wrong URL pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge = get_challenge_model(challenge_pk)

    challenge_phase_ids = challenge.challengephase_set.all().values_list('id', flat=True)

    q_params = {'challenge_phase__id__in': challenge_phase_ids}
    since_date = None
    if duration.lower() == 'daily':
        # Get the midnight time of the day
        since_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    elif duration.lower() == 'weekly':
        since_date = (timezone.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

    elif duration.lower() == 'monthly':
        since_date = (timezone.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    # for `all` we dont need any condition in `q_params`
    if since_date:
        q_params['submitted_at__gte'] = since_date

    submission_count = Submission.objects.filter(**q_params).count()
    submission_count = SubmissionCount(submission_count)
    serializer = SubmissionCountSerializer(submission_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_phase_submission_count_by_team(request, challenge_pk, challenge_phase_pk):
    """
    Returns number of submissions done by a participant team in a challenge phase
    """
    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    participant_team = get_participant_team_id_of_user_for_a_challenge(request.user, challenge.pk)

    submissions = Submission.objects.filter(
        challenge_phase=challenge_phase, challenge_phase__challenge=challenge, participant_team=participant_team)
    participant_team_submissions = submissions.count()

    challenge_phase_submission_count = ChallengePhaseSubmissionCount(
        participant_team_submissions, challenge_phase.pk)
    try:
        serializer = ChallengePhaseSubmissionCountSerializer(challenge_phase_submission_count)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        response_data = {'error': "Bad request. Please try again later!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_last_submission_time(request, challenge_pk, challenge_phase_pk, submission_by):
    """
        Returns the last submission time for a particular challenge phase
    """
    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    # To get the last submission time by a user in a challenge phase.
    if submission_by == 'user':
        last_submitted_at = Submission.objects.filter(created_by=request.user.pk,
                                                      challenge_phase=challenge_phase,
                                                      challenge_phase__challenge=challenge)
        last_submitted_at = last_submitted_at.order_by('-submitted_at')[0].created_at
        last_submitted_at = LastSubmissionDateTime(last_submitted_at)
        serializer = LastSubmissionDateTimeSerializer(last_submitted_at)
        return Response(serializer.data, status=status.HTTP_200_OK)

    else:
        response_data = {'error': 'Page not found!'}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_last_submission_datetime_analysis(request, challenge_pk, challenge_phase_pk):
    """
    API to fetch
    1. To get the last submission time in a challenge phase.
    2. To get the last submission time in a challenge.
    """

    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    submissions = Submission.objects.filter(
        challenge_phase__challenge=challenge)

    if not submissions:
        response_data = {
            'message': 'You dont have any submissions in this challenge!'
        }
        return Response(response_data, status.HTTP_200_OK)

    last_submission_timestamp_in_challenge = submissions.order_by(
        '-submitted_at')[0].created_at

    submissions_in_a_phase = submissions.filter(
        challenge_phase=challenge_phase)

    if not submissions_in_a_phase:
        last_submission_timestamp_in_challenge_phase = 'You dont have any submissions in this challenge phase!'
    else:
        last_submission_timestamp_in_challenge_phase = submissions_in_a_phase.order_by('-submitted_at')[0].created_at

    last_submission_timestamp = LastSubmissionTimestamp(
        last_submission_timestamp_in_challenge, last_submission_timestamp_in_challenge_phase, challenge_phase.pk)

    try:
        serializer = LastSubmissionTimestampSerializer(last_submission_timestamp)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        response_data = {'error': 'Bad request. Please try again later!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', ])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_phase_submission_analysis(request, challenge_pk, challenge_phase_pk):
    """
    Returns
    1. Total number of submissions in a challenge phase
    2. Number of teams which made submissions in a challenge phase
    3. Number of submissions with status a)Submitting, b)Submitted, c)Running, d)Failed, e)Cancelled, f)Finished status
    4. Number of flagged & public submissions in challenge phase
    """

    challenge = get_challenge_model(challenge_pk)
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)
    # Get the total submissions in a challenge phase
    submissions = Submission.objects.filter(
        challenge_phase=challenge_phase, challenge_phase__challenge=challenge)
    total_submissions = submissions.count()
    # Get the total participant teams in a challenge phase
    participant_team_count = submissions.values('participant_team').distinct().count()
    # Get flagged submission count
    flagged_submissions_count = submissions.filter(is_flagged=True).count()
    # Get public submission count
    public_submissions_count = submissions.filter(is_public=True).count()
    challenge_phase_submission_count = ChallengePhaseSubmissionAnalytics(total_submissions,
                                                                         participant_team_count,
                                                                         flagged_submissions_count,
                                                                         public_submissions_count,
                                                                         challenge_phase.pk)
    try:
        serializer = ChallengePhaseSubmissionAnalyticsSerializer(challenge_phase_submission_count)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except ValueError:
        response_data = {'error': 'Bad request. Please try again later!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
