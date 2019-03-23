import logging
import uuid

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.throttling import UserRateThrottle
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)

from .models import InviteUserToChallenge
from .permissions import HasVerifiedEmail
from .serializers import (
    InviteUserToChallengeSerializer,
    AcceptChallengeInvitationSerializer,
)
from base.utils import send_email
from challenges.utils import get_challenge_model
from hosts.utils import is_user_a_host_of_challenge
from hosts.models import ChallengeHost

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_auth_token(request):
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        response_data = {"error": "This User account doesn't exist."}
        Response(response_data, status.HTTP_404_NOT_FOUND)

    try:
        token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        token = Token.objects.create(user=user)
        token.save()

    response_data = {"token": "{}".format(token)}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def invite_users_to_challenge(request, challenge_pk):

    challenge = get_challenge_model(challenge_pk)

    try:
        challenge_host = ChallengeHost.objects.get(user=request.user.pk)
    except ChallengeHost.DoesNotExist:
        response_data = {"error": "You're not a challenge host"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_a_host_of_challenge(request.user, challenge.pk):
        response_data = {
            "error": "You're not authorized to invite a user in {}".format(
                challenge.title
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    users_email = request.data.get("emails")
    subject = request.data.get("subject")

    if not users_email or not subject:
        response_data = {
            "error": "Users email or subject field can't be blank"
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    users_email = eval(users_email)
    invalid_emails = []
    for email in users_email:
        try:
            invited_user = InviteUserToChallenge.objects.get(
                email=email, challenge=challenge.pk
            )
            invitation_key = invited_user.invitation_key
        except InviteUserToChallenge.DoesNotExist:
            user, created = User.objects.get_or_create(
                username=email, email=email
            )
            if created:
                EmailAddress.objects.create(
                    user=user, email=email, primary=True, verified=True
                )
            invitation_key = uuid.uuid4()
            invitation_status = "pending"
            data = {
                "email": email,
                "invitation_key": str(invitation_key),
                "status": invitation_status,
                "challenge": challenge.pk,
                "user": user.pk,
                "invited_by": challenge_host.pk,
            }
            serializer = InviteUserToChallengeSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
            else:
                invalid_emails.append(email)

        sender_email = settings.CLOUDCV_TEAM_EMAIL
        url = "{}/accept/invitation/{}/".format(
            settings.EVALAI_HOST_URL, invitation_key
        )
        context = {"title": challenge.title, "url": url}

        if email not in invalid_emails:
            send_email(
                subject,
                "challenge_invitation_email.html",
                sender_email,
                email,
                context,
            )

    if len(users_email) == len(invalid_emails):
        response_data = {"error": "Please enter correct email ids"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    response_data = {
        "success": "The invitation to register for {} is sent".format(
            challenge.title
        ),
        "invalid_emails": invalid_emails,
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET", "PUT"])
@throttle_classes([UserRateThrottle])
@permission_classes(())
def accept_challenge_invitation(request, invitation_key):
    try:
        invitation = InviteUserToChallenge.objects.get(
            invitation_key=invitation_key
        )
    except InviteUserToChallenge.DoesNotExist:
        response_data = {
            "error": "The invitation with key {} doesn't exist".format(
                invitation_key
            )
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        serializer = InviteUserToChallengeSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        serializer = AcceptChallengeInvitationSerializer(
            invitation.user, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            invitation.user.set_password(serializer.data.get("password"))
            invitation.user.save()
            invitation.status = "accepted"
            invitation.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
