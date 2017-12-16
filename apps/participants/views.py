from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail, BadHeaderError

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
from base.utils import paginated_queryset, encode_data, decode_data
from challenges.models import Challenge
from hosts.utils import is_user_a_host_of_challenge

from .models import (Participant, ParticipantTeam)
from .serializers import (ParticipantTeamSerializer,
                          ChallengeParticipantTeam,
                          ChallengeParticipantTeamList,
                          ChallengeParticipantTeamListSerializer,
                          ParticipantTeamDetailSerializer,)
from .utils import (get_list_of_challenges_for_participant_team,
                    get_list_of_challenges_participated_by_a_user,)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_list(request):

    if request.method == 'GET':
        participant_teams_id = Participant.objects.filter(user_id=request.user).values_list('team_id', flat=True)
        participant_teams = ParticipantTeam.objects.filter(
            id__in=participant_teams_id)
        paginator, result_page = paginated_queryset(participant_teams, request)
        serializer = ParticipantTeamDetailSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        serializer = ParticipantTeamSerializer(data=request.data,
                                               context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            participant_team = serializer.instance
            participant = Participant(user=request.user,
                                      status=Participant.SELF,
                                      team=participant_team)
            participant.save()
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_detail(request, pk):

    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        serializer = ParticipantTeamDetailSerializer(participant_team)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:

        if request.method == 'PATCH':
            serializer = ParticipantTeamSerializer(participant_team, data=request.data,
                                                   context={
                                                       'request': request},
                                                   partial=True)
        else:
            serializer = ParticipantTeamSerializer(participant_team, data=request.data,
                                                   context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        participant_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def email_invite_participant_to_team(request, pk):
    """
    Users can be invited to join the Participant team by sending a
    unique E-mail to the user being invited to. The E-mail of the user and the
    challenge host id is encoded and made into a url.
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data = {'error': 'User does not exist with this email address!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    invited_user_participated_challenges = get_list_of_challenges_participated_by_a_user(
        user).values_list("id", flat=True)
    team_participated_challenges = get_list_of_challenges_for_participant_team(
        [participant_team]).values_list("id", flat=True)

    if set(invited_user_participated_challenges) & set(team_participated_challenges):
        """
        Condition to check if the user has already participated in challenges where
        the inviting participant has participated. If this is the case,
        then the user cannot be invited since he cannot participate in a challenge
        via two teams.
        """
        response_data = {'error': 'Sorry, cannot invite user to the team!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
    if request.user.email == email:
        response_data = {'error': 'A participant cannot invite himself'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    team_hash, email_hash = encode_data([str(pk), email])
    unique_hash = "{}/{}".format(team_hash, email_hash)
    url = request.data['url'].split("team")[0]
    full_url = "{}invitation/{}".format(url, unique_hash)
    team_name = participant_team.team_name
    body = "You've been invited to join team {}. " \
           "Click the bottom link to accept the " \
           "invitation and to participate in challenges. \n{}"
    message = body.format(team_name, full_url)
    subject = "You have been invited to join {} team at CloudCV!".format(team_name)
    try:
        send_mail(subject,
                  message,
                  settings.ADMIN_EMAIL,
                  [email],
                  fail_silently=False,)
        response_message = "{} has been invited to join team {}".format(email, team_name)
        response_data = {'message': response_message}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    except BadHeaderError:
        response_data = {'error': 'There was some error while sending the invite.'}
        return Response(response_data, status=status.HTTP_417_EXPECTATION_FAILED)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def invitation_accepted(request, team_hash, email_hash):
    """
    Decodes the data from the URL when the invited participant clicks on the URL
    given in the invite E-mail and adds the user to the corresponding participant
    team
    """
    pk, accepted_user_email = decode_data([team_hash, email_hash])
    current_user_email = request.user.email
    participant_team = ParticipantTeam.objects.get(pk=int(pk))
    if current_user_email == accepted_user_email:
        Participant.objects.get_or_create(user=User.objects.get(email=accepted_user_email),
                                          status=Participant.ACCEPTED,
                                          team=participant_team)
        response_data = {'message': 'You have been successfully added to the team!'}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    response_data = {'error': 'You aren\'t authorized!'}
    return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@throttle_classes([UserRateThrottle])
@api_view(['DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def delete_participant_from_team(request, participant_team_pk, participant_pk):
    """
    Deletes a participant from a Participant Team
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant = Participant.objects.get(pk=participant_pk)
    except Participant.DoesNotExist:
        response_data = {'error': 'Participant does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if participant_team.created_by == request.user:

        if participant.user == request.user:  # when the user tries to remove himself
            response_data = {
                'error': 'You are not allowed to remove yourself since you are admin. Please delete the team if you want to do so!'}  # noqa: ignore=E501
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            participant.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        response_data = {
            'error': 'Sorry, you do not have permissions to remove this participant'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_teams_and_corresponding_challenges_for_a_participant(request, challenge_pk):
    """
    Returns list of teams and corresponding challenges for a participant
    """
    # first get list of all the participants and teams related to the user
    participant_objs = Participant.objects.filter(user=request.user).prefetch_related('team')

    is_challenge_host = is_user_a_host_of_challenge(user=request.user, challenge_pk=challenge_pk)

    challenge_participated_teams = []
    for participant_obj in participant_objs:
        participant_team = participant_obj.team

        challenges = Challenge.objects.filter(
            participant_teams=participant_team)

        if challenges.count():
            for challenge in challenges:
                challenge_participated_teams.append(ChallengeParticipantTeam(
                    challenge, participant_team))
        else:
            challenge = None
            challenge_participated_teams.append(ChallengeParticipantTeam(
                challenge, participant_team))
    serializer = ChallengeParticipantTeamListSerializer(ChallengeParticipantTeamList(challenge_participated_teams))
    response_data = serializer.data
    response_data['is_challenge_host'] = is_challenge_host
    return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['DELETE', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def remove_self_from_participant_team(request, participant_team_pk):
    """
    A user can remove himself from the participant team.
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant = Participant.objects.get(user=request.user, team__pk=participant_team_pk)
    except:
        response_data = {'error': 'Sorry, you do not belong to this team!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if get_list_of_challenges_for_participant_team([participant_team]).exists():
        response_data = {'error': 'Sorry, you cannot delete this team since it has taken part in challenge(s)!'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    else:
        participant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
