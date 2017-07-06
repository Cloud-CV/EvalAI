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
from challenges.utils import get_challenge_model

from participants.serializers import (ParticipantTeamCount,
                                      ParticipantTeamCountSerializer,
                                      )


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
