from django.conf import settings
from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)

from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail
from challenges.models import (
    ChallengePhase,
    Challenge,)
from participants.models import (ParticipantTeam, Participant)
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge,
    is_user_part_of_participant_team,)

from .models import Submission
from .serializers import SubmissionSerializer


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_submission(request, challenge_id, challenge_phase_id):
    """API Endpoint for making a submission to a challenge"""
    # check if the challenge exists or not
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # check if the challenge is active or not
    if not challenge.is_active:
        response_data = {'error': 'Challenge is not active!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # check if the challenge phase exists or not
    try:
        challenge_phase = ChallengePhase.objects.get(
            pk=challenge_phase_id, challenge=challenge)
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'Challenge Phase does not exist!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # check if challenge phase is public and accepting solutions
    if not challenge_phase.is_public:
        response_data = {
            'error': 'Sorry, cannot accept submissions since challenge phase is not public!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        request.user, challenge_id)

    if participant_team_id is None:
        response_data = {'error': 'You haven\'t participated in the challenge'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_id)
    except Participant.DoesNotExist:
        response_data = {'error': 'Participant Team not found!'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)

    serializer = SubmissionSerializer(data=request.data,
                                      context={'participant_team': participant_team,
                                               'challenge_phase': challenge_phase,
                                               'request': request
                                               })
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        print response_data
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
