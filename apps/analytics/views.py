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
from challenges.utils import get_challenge_phase_model
from jobs.models import Submission

from .serializers import SubmissionStats, SubmissionStatsSerializer


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_submission_stats(request, challenge_phase_pk):
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)
    submission_total = Submission.objects.filter(challenge_phase=challenge_phase).count()
    submission_stats = SubmissionStats(submission_total)
    serializer = SubmissionStatsSerializer(submission_stats)
    return Response(serializer.data, status=status.HTTP_200_OK)
