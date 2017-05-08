from rest_framework import status
from rest_framework.response import Response
from challenges.models import (
    ChallengePhase,
    Challenge,
    )
from participants.models import (ParticipantTeam,)


def get_challenge_object(challenge_pk):    
    try:
        Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


def get_challenge_phase_object(challenge_phase_pk):
    try:
        challenge_phase = ChallengePhase.objects.get(pk=challenge_phase_pk)
        return challenge_phase
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'Challenge Phase does not exist'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


def get_participant_team_object(participant_team_pk):
    try:
        ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'Participant team does not exist'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
