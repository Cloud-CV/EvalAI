from django.contrib.auth.models import User
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.conf import settings


from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail
from base.utils import paginated_queryset
from .models import ChallengeHost, ChallengeHostTeam
from .serializers import (
    ChallengeHostSerializer,
    ChallengeHostTeamSerializer,
    InviteHostToTeamSerializer,
    HostTeamDetailSerializer,
)
from .utils import host_invitations_token_generator, is_user_part_of_host_team




@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_host_team_list(request):

    if request.method == "GET":
        challenge_host_team_ids = ChallengeHost.objects.filter(
            user=request.user
        ).values_list("team_name", flat=True)
        challenge_host_teams = ChallengeHostTeam.objects.filter(
            id__in=challenge_host_team_ids
        ).order_by("-id")
        paginator, result_page = paginated_queryset(
            challenge_host_teams, request
        )
        serializer = HostTeamDetailSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == "POST":
        serializer = ChallengeHostTeamSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_host_team_detail(request, pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        serializer = HostTeamDetailSerializer(challenge_host_team)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:

        if request.method == "PATCH":
            serializer = ChallengeHostTeamSerializer(
                challenge_host_team,
                data=request.data,
                context={"request": request},
                partial=True,
            )
        else:
            serializer = ChallengeHostTeamSerializer(
                challenge_host_team,
                data=request.data,
                context={"request": request},
            )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    elif request.method == "DELETE":
        challenge_host_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_host_list(request, challenge_host_team_pk):

    try:
        challenge_host_team = ChallengeHostTeam.objects.get(
            pk=challenge_host_team_pk
        )
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        challenge_host_status = request.query_params.get("status", None)
        filter_condition = {
            "team_name": challenge_host_team,
            "user": request.user,
        }
        if challenge_host_status:
            challenge_host_status = challenge_host_status.split(",")
            filter_condition.update({"status__in": challenge_host_status})

        challenge_host = ChallengeHost.objects.filter(
            **filter_condition
        ).order_by("-id")
        paginator, result_page = paginated_queryset(challenge_host, request)
        serializer = ChallengeHostSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == "POST":
        serializer = ChallengeHostSerializer(
            data=request.data,
            context={
                "challenge_host_team": challenge_host_team,
                "request": request,
            },
        )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_host_detail(request, challenge_host_team_pk, pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(
            pk=challenge_host_team_pk
        )
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        challenge_host = ChallengeHost.objects.get(pk=pk)
    except ChallengeHost.DoesNotExist:
        response_data = {"error": "ChallengeHost does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        serializer = ChallengeHostSerializer(challenge_host)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:
        if request.method == "PATCH":
            serializer = ChallengeHostSerializer(
                challenge_host,
                data=request.data,
                context={
                    "challenge_host_team": challenge_host_team,
                    "request": request,
                },
                partial=True,
            )
        else:
            serializer = ChallengeHostSerializer(
                challenge_host,
                data=request.data,
                context={
                    "challenge_host_team": challenge_host_team,
                    "request": request,
                },
            )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    elif request.method == "DELETE":
        challenge_host.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_challenge_host_team(request):

    serializer = ChallengeHostTeamSerializer(
        data=request.data, context={"request": request}
    )
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        challenge_host_team = serializer.instance
        challenge_host = ChallengeHost(
            user=request.user,
            status=ChallengeHost.SELF,
            permissions=ChallengeHost.ADMIN,
            team_name=challenge_host_team,
        )
        challenge_host.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def remove_self_from_challenge_host_team(request, challenge_host_team_pk):
    """
    A user can remove himself from the challenge host team.
    """
    try:
        ChallengeHostTeam.objects.get(pk=challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "ChallengeHostTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
    try:
        challenge_host = ChallengeHost.objects.filter(
            user=request.user.id, team_name__pk=challenge_host_team_pk
        )
        challenge_host.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except:  # noqa E722
        response_data = {"error": "Sorry, you do not belong to this team."}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def invite_host_to_team(request, pk):

    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "Host Team does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    email = request.data.get("email")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data = {
            "error": "User does not exist with this email address!"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check if the user requesting this API is part of host team
    if not is_user_part_of_host_team(request.user, challenge_host_team):
        response_data = {"error": "You are not a member of this team!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    host = ChallengeHost.objects.filter(
        team_name=challenge_host_team, user=user
    )

    if host.exists():
        response_data = {"error": "User is already part of the team!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    user_data = {
        "user": user,
        "challenge_host_team": challenge_host_team
    }
    token = host_invitations_token_generator.make_token(user_data)
    link = "{}/accept-host-invitation/{}/{}".format(settings.HOSTNAME, token, pk)
    print(link)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def add_self_to_host_team(request, challenge_host_team_pk, host_invitation_token):
    "localhost:8888/accept-host-invitation/5e6-24d0166438fbfcc2ae11/2"
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {"error": "Host Team does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    user = User.objects.get(username=request.user)

    user.is_user_host = is_user_part_of_host_team(user, challenge_host_team)
    if user.is_user_host:
        response_data = {"error": "You are already part of the host team - {}".format(challenge_host_team.team_name)}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    user_data = {
        "user": user,
        "challenge_host_team": challenge_host_team
    }

    if host_invitations_token_generator.check_token(user_data, host_invitation_token):

        serializer = InviteHostToTeamSerializer(
            data={
                "email": user.email
            },
            context={
                "challenge_host_team": challenge_host_team,
                "request": request
            }
        )

        if serializer.is_valid():
            serializer.save()
            response_data = {
                "error": "You are already part of the host team - {}".format(challenge_host_team.team_name)
            }
            return Response(
                response_data, status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        response_data = {"error": "Could not join host team, invalid or expired URL."}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
