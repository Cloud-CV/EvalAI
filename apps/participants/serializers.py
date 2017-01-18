from django.contrib.auth.models import User

from rest_framework import serializers

from challenges.serializers import ChallengeSerializer
from .models import (Participant, ParticipantTeam)


class ParticipantTeamSerializer(serializers.ModelSerializer):

    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    def __init__(self, *args, **kwargs):
        super(ParticipantTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            kwargs['data']['created_by'] = request.user.username

    class Meta:
        model = ParticipantTeam
        fields = ('id', 'team_name', 'created_by')


class InviteParticipantToTeamSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super(InviteParticipantToTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            self.participant_team = context.get('participant_team')
            self.user = context.get('request').user

    def validate_email(self, value):
        if value == self.user.email:
            raise serializers.ValidationError('A participant cannot invite himself')
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist')
        return value

    def save(self):
        email = self.validated_data.get('email')
        return Participant.objects.get_or_create(user=User.objects.get(email=email),
                                                 status=Participant.ACCEPTED,
                                                 team=self.participant_team)


class ParticipantSerializer(serializers.ModelSerializer):

    member_name = serializers.SerializerMethodField()
    member_id = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ('member_name', 'status', 'member_id')

    def get_member_name(self, obj):
        return obj.user.username

    def get_member_id(self, obj):
        return obj.user.id


# Serializer for Participant Teams and Participant Combined
class ParticipantsBasedOnParticipantTeamSerializer(serializers.ModelSerializer):

    members = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = ParticipantTeam
        fields = ('id', 'team_name', 'created_by', 'members')

    def get_members(self, obj):
        participants = Participant.objects.filter(team__pk=obj.id)
        serializer = ParticipantSerializer(participants, many=True)
        return serializer.data


# Serializer to map Challenge and Participant Teams ####
class ChallengeParticipantTeam(object):

    def __init__(self, challenge, participant_team):
        self.challenge = challenge
        self.participant_team = participant_team


class ChallengeParticipantTeamSerializer(serializers.Serializer):
    challenge = ChallengeSerializer()
    participant_team = ParticipantTeamSerializer()


class ChallengeParticipantTeamList(object):

    def __init__(self, challenge_participant_team_list):
        self.challenge_participant_team_list = challenge_participant_team_list


class ChallengeParticipantTeamListSerializer(serializers.Serializer):
    challenge_participant_team_list = ChallengeParticipantTeamSerializer(many=True)
