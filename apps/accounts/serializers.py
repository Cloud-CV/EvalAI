from django.contrib.auth import get_user_model


from rest_framework import serializers

from .models import InviteUserToChallenge


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Make username as a read_only field.
    """

    class Meta:
        model = get_user_model()
        fields = ("pk", "email", "username", "first_name", "last_name")
        read_only_fields = ("email", "username")


class ProfileSerializer(UserDetailsSerializer):
    """
    Serializer to update the user profile.
    """

    affiliation = serializers.CharField(source="profile.affiliation")

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ("affiliation",)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        affiliation = profile_data.get("affiliation")

        instance = super(ProfileSerializer, self).update(
            instance, validated_data
        )

        profile = instance.profile
        if profile_data and affiliation:
            profile.affiliation = affiliation
            profile.save()
        return instance


class InviteUserToChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer to store the invitation details
    """

    challenge_title = serializers.SerializerMethodField()
    challenge_host_team_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = InviteUserToChallenge
        fields = (
            "email",
            "invitation_key",
            "status",
            "challenge",
            "user",
            "challenge_title",
            "challenge_host_team_name",
            "username",
        )

    def get_challenge_title(self, obj):
        return obj.challenge.title

    def get_challenge_host_team_name(self, obj):
        return obj.challenge.creator.team_name

    def get_username(self, obj):
        return obj.user.username


class AcceptChallengeInvitationSerializer(serializers.ModelSerializer):
    """
    Serializer to accept challenge invitation
    """

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "password")
