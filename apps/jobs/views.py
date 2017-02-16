from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)

from django.db.models.expressions import RawSQL
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

import challenges.constants as constants

from accounts.permissions import HasVerifiedEmail
from base.utils import paginated_queryset
from challenges.models import (
    ChallengePhase,
    Challenge,
    ChallengePhaseSplit,
    LeaderboardData,)
from participants.models import (ParticipantTeam,)
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge,)

from .models import Submission
from .sender import publish_submission_message
from .serializers import SubmissionSerializer, LeaderboardDataSerializer


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


@throttle_classes([AnonRateThrottle])
@api_view(['GET'])
def leaderboard(request, challenge_phase_split_id):
    """
    Returns leaderboard for a corresponding Challenge Phase Split
    """

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
    leaderboard_data = LeaderboardData.objects.filter(challenge_phase_split=challenge_phase_split).annotate(filtering_score=RawSQL(
        'result->>%s', (default_order_by, ))).order_by('submission__participant_team', '-filtering_score').distinct('submission__participant_team')

    # If number of entries in the leaderboard data is more than number of rows allowed in leaderboard,
    # then choose the `TOP N` entries from the table

    if leaderboard_data.count() >= constants.NUMBER_OF_ROWS_IN_LEADERBOARD:
        leaderboard_data = leaderboard_data[:constants.NUMBER_OF_ROWS_IN_LEADERBOARD]

    # print leaderboard_data
    paginator, result_page = paginated_queryset(leaderboard_data, request)
    try:
        serializer = LeaderboardDataSerializer(result_page, many=True)
        print serializer.is_valid()
        print serializer.errors
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)
    except:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
