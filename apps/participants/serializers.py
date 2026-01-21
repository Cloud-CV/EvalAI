from accounts.models import Profile
from accounts.serializers import UserProfileSerializer
from challenges.models import Challenge
from challenges.serializers import ChallengeSerializer
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import Participant, ParticipantTeam


class ParticipantTeamSerializer(serializers.ModelSerializer):
    """Serializer class to map Participants to Teams."""

    created_by = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            request = context.get("request")
            kwargs["data"]["created_by"] = request.user.username

    class Meta:
        """Meta class for ParticipantTeamSerializer."""
        model = ParticipantTeam
        fields = ("id", "team_name", "created_by", "team_url")


class InviteParticipantToTeamSerializer(serializers.Serializer):
    """Serializer class for inviting Participant to Team."""

    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            self.participant_team = context.get("participant_team")
            self.user = context.get("request").user

    def validate_email(self, value):
        """Validate email for participant invitation."""
        if value == self.user.email:
            raise serializers.ValidationError(
                "A participant cannot invite himself"
            )
        try:
            User.objects.get(email=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("User does not exist") from exc
        return value

    def save(self, **kwargs):
        """Save method for creating participant."""
        email = self.validated_data.get("email")
        return Participant.objects.get_or_create(
            user=User.objects.get(email=email),
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )


class ParticipantSerializer(serializers.ModelSerializer):
    """Serializer class for Participants."""

    member_name = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        """Meta class for ParticipantSerializer."""
        model = Participant
        fields = (
            "member_name",
            "first_name",
            "last_name",
            "email",
            "status",
            "profile",
        )

    @staticmethod
    def get_member_name(obj):
        """Get username of participant."""
        return obj.user.username

    @staticmethod
    def get_first_name(obj):
        """Get first name of participant."""
        return obj.user.first_name

    @staticmethod
    def get_last_name(obj):
        """Get last name of participant."""
        return obj.user.last_name

    @staticmethod
    def get_email(obj):
        """Get email of participant."""
        return obj.user.email

    @staticmethod
    def get_profile(obj):
        """Get profile of participant."""
        user_profile = Profile.objects.get(user=obj.user)
        serializer = UserProfileSerializer(user_profile)
        return serializer.data


class ParticipantTeamDetailSerializer(serializers.ModelSerializer):
    """Serializer for Participant Teams and Participant Combined."""

    members = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    class Meta:
        """Meta class for ParticipantTeamDetailSerializer."""
        model = ParticipantTeam
        fields = ("id", "team_name", "created_by", "members", "team_url")

    @staticmethod
    def get_members(obj):
        """Get all members of a team."""
        participants = Participant.objects.filter(team__pk=obj.id)
        serializer = ParticipantSerializer(participants, many=True)
        return serializer.data


class ChallengeParticipantTeam:
    """Serializer to map Challenge and Participant Teams."""

    def __init__(self, challenge, participant_team):
        """Initialize with challenge and participant team."""
        self.challenge = challenge
        self.participant_team = participant_team


class ChallengeParticipantTeamSerializer(serializers.Serializer):
    """Serializer to initialize Challenge and Participant's Team."""

    challenge = ChallengeSerializer()
    participant_team = ParticipantTeamSerializer()


class ChallengeParticipantTeamList:
    """Class to create a list of Challenge and Participant Teams."""

    def __init__(self, challenge_participant_team_list):
        """Initialize with challenge participant team list."""
        self.challenge_participant_team_list = challenge_participant_team_list


class ChallengeParticipantTeamListSerializer(serializers.Serializer):
    """Serializer to map a challenge's participant team lists."""

    challenge_participant_team_list = ChallengeParticipantTeamSerializer(
        many=True
    )
    datetime_now = serializers.SerializerMethodField()

    @staticmethod
    def get_datetime_now(obj):
        """Get current datetime."""
        return timezone.now()


class ParticipantTeamCount:
    """Class to hold participant team count."""

    def __init__(self, participant_team_count):
        """Initialize with participant team count."""
        self.participant_team_count = participant_team_count


class ParticipantTeamCountSerializer(serializers.Serializer):
    """Serializer for participant team count."""
    participant_team_count = serializers.IntegerField()


class ParticipantCount:
    """Class to hold participant count."""

    def __init__(self, participant_count):
        """Initialize with participant count."""
        self.participant_count = participant_count


class ParticipantCountSerializer(serializers.Serializer):
    """Serializer for participant count."""
    participant_count = serializers.IntegerField()


class ChallengeParticipantSerializer(serializers.Serializer):
    """Serializer for challenge participants."""
    team_name = serializers.SerializerMethodField()
    team_members = serializers.SerializerMethodField()
    team_members_email_ids = serializers.SerializerMethodField()

    class Meta:
        """Meta class for ChallengeParticipantSerializer."""
        model = Challenge
        fields = ("team_name", "team_members", "team_members_email_ids")

    @staticmethod
    def get_team_name(obj):
        """Get team name."""
        return obj.team_name

    @staticmethod
    def get_team_members(obj):
        """Get team members' usernames."""
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.team_name
            )
        except ParticipantTeam.DoesNotExist:
            return "Participant team does not exist"

        participant_ids = Participant.objects.filter(
            team=participant_team
        ).values_list("user_id", flat=True)
        return list(
            User.objects.filter(id__in=participant_ids).values_list(
                "username", flat=True
            )
        )

    @staticmethod
    def get_team_members_email_ids(obj):
        """Get team members' email ids."""
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.team_name
            )
        except ParticipantTeam.DoesNotExist:
            return "Participant team does not exist"

        participant_ids = Participant.objects.filter(
            team=participant_team
        ).values_list("user_id", flat=True)
        return list(
            User.objects.filter(id__in=participant_ids).values_list(
                "email", flat=True
            )
        )
