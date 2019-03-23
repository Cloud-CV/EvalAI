from django.contrib.auth import get_user_model

from rest_framework import serializers


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
