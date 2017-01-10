from django.conf import settings
from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,)
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail

from participants.utils import (
    get_participant_team_id_of_a_user_for_a_challenge,
    check_user_participated_in_challenge,)

from challenges.models import (
    ChallengePhase,
    Challenge,)
from participants.models import (ParticipantTeam, Participant)

from .models import Submission


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_submission(request, challenge_id, challenge_phase_id):
    """API Endpoint for making a submission to a challenge"""
    # check if the challenge exists or not
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
        if not challenge.is_active():
            response_data = {'error': 'Challenge is not active!'}
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    # check if the challenge phase exists or not
    try:
        challenge_phase = ChallengePhase.objects.get(
            pk=challenge_phase_id, challenge=challenge)
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'Challenge Phase does not exist!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    # check if challenge is public and accepting solutions
    if not challenge.is_public:
        response_data = {
            'error': 'Sorry, cannot accept submissions since challenge is not public!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    # check if challenge phase is public and accepting solutions
    if not challenge_phase.is_public:
        response_data = {
            'error': 'Sorry, cannot accept submissions since challenge phase is not public!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    # participant team exists and has participated in the challenge
    if not check_user_participated_in_challenge(request.user, challenge_id):
        response_data = {'error': 'You haven\'t participated in the challenge'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    participant_team_id = get_participant_team_id_of_a_user_for_a_challenge(
        request.user, challenge_id)

    try:
        participant_team = Participant.objects.get(pk=participant_team_id)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'Participant Team not found!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    Submission.objects.create(
        challenge_phase=challenge_phase, challenge=challenge, participated_team=participant_team)

    response_data = {'message': 'Submission done successfully!'}
    return Response(response_data, status=status.HTTP_201_CREATED)
