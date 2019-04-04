from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import serializers

from challenges.serializers import ChallengeSerializer
from .models import Participant, ParticipantTeam


class ParticipantTeamSerializer(serializers.ModelSerializer):
    """Serializer class to map Participants to Teams."""

    created_by = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super(ParticipantTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            request = context.get("request")
            kwargs["data"]["created_by"] = request.user.username

    class Meta:
        model = ParticipantTeam
        fields = ("id", "team_name", "created_by", "team_url")


class InviteParticipantToTeamSerializer(serializers.Serializer):
    """Serializer class for inviting Participant to Team."""

    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super(InviteParticipantToTeamSerializer, self).__init__(
            *args, **kwargs
        )
        context = kwargs.get("context")
        if context:
            self.participant_team = context.get("participant_team")
            self.user = context.get("request").user

    def validate_email(self, value):
        if value == self.user.email:
            raise serializers.ValidationError(
                "A participant cannot invite himself"
            )
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value

    def save(self):
        email = self.validated_data.get("email")
        return Participant.objects.get_or_create(
            user=User.objects.get(email=email),
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )


class ParticipantSerializer(serializers.ModelSerializer):
    """Serializer class for Participants."""

    member_name = serializers.SerializerMethodField()
    member_id = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ("member_name", "status", "member_id")

    def get_member_name(self, obj):
        return obj.user.username

    def get_member_id(self, obj):
        return obj.user.id


class ParticipantTeamDetailSerializer(serializers.ModelSerializer):
    """Serializer for Participant Teams and Participant Combined."""

    members = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    class Meta:
        model = ParticipantTeam
        fields = ("id", "team_name", "created_by", "members", "team_url")

    def get_members(self, obj):
        participants = Participant.objects.filter(team__pk=obj.id)
        serializer = ParticipantSerializer(participants, many=True)
        return serializer.data


class ChallengeParticipantTeam(object):
    """Serializer to map Challenge and Participant Teams."""

    def __init__(self, challenge, participant_team):
        self.challenge = challenge
        self.participant_team = participant_team


class ChallengeParticipantTeamSerializer(serializers.Serializer):
    """Serializer to initialize Challenge and Participant's Team"""

    challenge = ChallengeSerializer()
    participant_team = ParticipantTeamSerializer()


class ChallengeParticipantTeamList(object):
    """Class to create a list of Challenge and Participant Teams."""

    def __init__(self, challenge_participant_team_list):
        self.challenge_participant_team_list = challenge_participant_team_list


class ChallengeParticipantTeamListSerializer(serializers.Serializer):
    """Serializer to map a challenge's participant team lists."""

    challenge_participant_team_list = ChallengeParticipantTeamSerializer(
        many=True
    )
    datetime_now = serializers.SerializerMethodField()

    def get_datetime_now(self, obj):
        return timezone.now()


class ParticipantTeamCount(object):
    def __init__(self, participant_team_count):
        self.participant_team_count = participant_team_count


class ParticipantTeamCountSerializer(serializers.Serializer):
    participant_team_count = serializers.IntegerField()


class ParticipantCount(object):
    def __init__(self, participant_count):
        self.participant_count = participant_count


class ParticipantCountSerializer(serializers.Serializer):
    participant_count = serializers.IntegerField()
