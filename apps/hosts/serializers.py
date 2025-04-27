from django.contrib.auth.models import User
from rest_framework import serializers

from .models import ChallengeHost, ChallengeHostTeam


class ChallengeHostTeamSerializer(serializers.ModelSerializer):
    """Serializer for the ChallengeHostTeam model."""

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
        model = ChallengeHostTeam
        fields = ("id", "team_name", "created_by", "team_url")


class ChallengeHostSerializer(serializers.ModelSerializer):
    """Serializer for the ChallengeHost model."""

    status = serializers.ChoiceField(choices=ChallengeHost.STATUS_OPTIONS)
    permissions = serializers.ChoiceField(
        choices=ChallengeHost.PERMISSION_OPTIONS
    )
    user = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            challenge_host_team = context.get("challenge_host_team")
            request = context.get("request")
            kwargs["data"]["team_name"] = challenge_host_team.pk
            kwargs["data"]["user"] = request.user.username

    class Meta:
        model = ChallengeHost
        fields = ("id", "user", "team_name", "status", "permissions")


class InviteHostToTeamSerializer(serializers.Serializer):
    """Serializer for inviting a host to join a team."""

    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            self.challenge_host_team = context.get("challenge_host_team")
            self.user = context.get("request").user

    def validate_email(self, value):
        """Validate the email to ensure it 
        doesn't belong to the inviting user."""
        if value == self.user.email:
            raise serializers.ValidationError("A host cannot invite himself")
        try:
            User.objects.get(email=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("User does not exist") from exc
        return value

    def save(self, **kwargs):
        """Create or get a ChallengeHost for the invited user."""
        email = self.validated_data.get("email")
        return ChallengeHost.objects.get_or_create(
            user=User.objects.get(email=email),
            status=ChallengeHost.ACCEPTED,
            team_name=self.challenge_host_team,
            permissions=ChallengeHost.WRITE,
        )


class HostTeamDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed information about host teams."""

    members = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    class Meta:
        model = ChallengeHostTeam
        fields = ("id", "team_name", "created_by", "members", "team_url")

    @staticmethod
    def get_members(obj):
        """Get all members of a host team."""
        hosts = ChallengeHost.objects.filter(team_name_id=obj.id)
        serializer = ChallengeHostSerializer(hosts, many=True)
        return serializer.data
