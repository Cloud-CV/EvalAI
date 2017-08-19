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

from base.utils import paginated_queryset
from challenges.permissions import IsChallengeCreator
from challenges.utils import get_challenge_model, get_challenge_phase_model
from hosts.utils import is_user_a_host_of_challenge
from jobs.models import Submission
from jobs.serializers import (SubmissionCount,
                              SubmissionCountSerializer,
                              )
from participants.models import Participant
from participants.serializers import (ParticipantCount,
                                      ParticipantCountSerializer,
                                      ParticipantTeamCount,
                                      ParticipantTeamCountSerializer,
                                      )
from participants.utils import (has_user_participated_in_challenge,
                                get_participant_team_id_of_user_for_a_challenge)
from .serializers import ChallengePhaseSubmissionAnalysisSerializer



@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_team_count(request, challenge_pk):
    challenge = get_challenge_model(challenge_pk)
    participant_team_count = challenge.participant_teams.count()
    participant_team_count = ParticipantTeamCount(participant_team_count)
    serializer = ParticipantTeamCountSerializer(participant_team_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_count(request, challenge_pk):
    challenge = get_challenge_model(challenge_pk)
    participant_teams = challenge.participant_teams.all()
    participant_count = Participant.objects.filter(team__in=participant_teams).count()
    participant_count = ParticipantCount(participant_count)
    serializer = ParticipantCountSerializer(participant_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_submission_count(request, challenge_pk, duration):
    '''
        Returns submission count for a challenge according to the duration
        Valid values for duration are all, daily, weekly and monthly.
    '''
    # make sure that a valid url is requested.
    if duration.lower() not in ('all', 'daily', 'weekly', 'monthly'):
        response_data = {'error': 'Wrong URL pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge = get_challenge_model(challenge_pk)

    challenge_phase_ids = challenge.challengephase_set.all().values_list('id', flat=True)

    q_params = {'challenge_phase__id__in': challenge_phase_ids}
    since_date = None
    if duration.lower() == 'daily':
        since_date = timezone.now().date()

    elif duration.lower() == 'weekly':
        since_date = (timezone.now() - timedelta(days=7)).date()

    elif duration.lower() == 'monthly':
        since_date = (timezone.now() - timedelta(days=30)).date()
    # for `all` we dont need any condition in `q_params`
    if since_date:
        q_params['submitted_at__gte'] = since_date

    submission_count = Submission.objects.filter(**q_params).count()
    submission_count = SubmissionCount(submission_count)
    serializer = SubmissionCountSerializer(submission_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_phase_submission_analysis(request, challenge_pk, challenge_phase_pk):

    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    submissions = Submission.objects.filter(challenge_phase__challenge=challenge,
                                            challenge_phase=challenge_phase)
    try:
        serializer = ChallengePhaseSubmissionAnalysisSerializer(submissions, many=True)
        response_data = serializer.data[0]
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
