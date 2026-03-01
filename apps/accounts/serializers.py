from allauth.account.models import EmailAddress
from base.utils import get_user_by_email
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from participants.utils import (
    has_participated_in_require_complete_profile_challenge,
)
from rest_auth.serializers import PasswordResetSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import JwtToken, Profile

LOCKED_PROFILE_FIELDS = [
    "first_name",
    "last_name",
    "address_street",
    "address_city",
    "address_state",
    "address_country",
    "university",
]


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Make username as a read_only field.
    """

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        read_only_fields = ("email", "username")


class ProfileSerializer(UserDetailsSerializer):
    """
    Serializer to update the user profile.
    """

    affiliation = serializers.CharField(
        source="profile.affiliation", allow_blank=True
    )
    github_url = serializers.URLField(
        source="profile.github_url", allow_blank=True
    )
    google_scholar_url = serializers.URLField(
        source="profile.google_scholar_url", allow_blank=True
    )
    linkedin_url = serializers.URLField(
        source="profile.linkedin_url", allow_blank=True
    )
    # Student profile fields
    address_street = serializers.CharField(
        source="profile.address_street", allow_blank=True, required=False
    )
    address_city = serializers.CharField(
        source="profile.address_city", allow_blank=True, required=False
    )
    address_state = serializers.CharField(
        source="profile.address_state", allow_blank=True, required=False
    )
    address_country = serializers.CharField(
        source="profile.address_country", allow_blank=True, required=False
    )
    university = serializers.CharField(
        source="profile.university", allow_blank=True, required=False
    )
    is_profile_complete = serializers.SerializerMethodField()
    is_profile_fields_locked = serializers.SerializerMethodField()
    email_bounced = serializers.BooleanField(
        source="profile.email_bounced", read_only=True
    )

    class Meta(UserDetailsSerializer.Meta):
        fields = (
            "pk",
            "email",
            "username",
            "first_name",
            "last_name",
            "affiliation",
            "github_url",
            "google_scholar_url",
            "linkedin_url",
            "address_street",
            "address_city",
            "address_state",
            "address_country",
            "university",
            "is_profile_complete",
            "is_profile_fields_locked",
            "email_bounced",
        )

    def get_is_profile_fields_locked(self, obj):
        """True if user has participated in a challenge requiring complete profile."""
        return self._is_profile_fields_locked()

    def get_is_profile_complete(self, obj):
        """Returns whether the user's profile is complete."""
        if hasattr(obj, "profile"):
            return obj.profile.is_complete
        return False

    def _is_profile_fields_locked(self):
        """Check if the user being updated has locked profile fields.
        Caches the result to avoid redundant DB queries within a single
        request (called from validate, update, and get_is_profile_fields_locked).
        """
        if not hasattr(self, "_cached_is_profile_fields_locked"):
            if self.instance and hasattr(self.instance, "pk"):
                self._cached_is_profile_fields_locked = (
                    has_participated_in_require_complete_profile_challenge(
                        self.instance
                    )
                )
            else:
                self._cached_is_profile_fields_locked = False
        return self._cached_is_profile_fields_locked

    def validate(self, attrs):
        """
        Validate that required profile fields cannot be blank.
        Participants must have complete profile (first_name, last_name,
        address_street, address_city, address_state, address_country, university).
        If user has participated in a require_complete_profile challenge,
        these fields cannot be edited.
        """
        errors = {}

        # Reject edits to locked fields (participated in
        # require_complete_profile).
        if self._is_profile_fields_locked():
            profile_data = attrs.get("profile", {})
            for field in LOCKED_PROFILE_FIELDS:
                if field in ["first_name", "last_name"]:
                    new_value = attrs.get(field)
                    current = (
                        getattr(self.instance, field, None)
                        if self.instance
                        else None
                    )
                else:
                    new_value = profile_data.get(field)
                    current = None
                    if self.instance and hasattr(self.instance, "profile"):
                        current = getattr(self.instance.profile, field, None)
                if new_value is not None:
                    new_str = str(new_value).strip() if new_value else ""
                    current_str = str(current).strip() if current else ""
                    if new_str != current_str:
                        errors[field] = [
                            "This field cannot be edited while participating "
                            "in an active challenge that requires complete "
                            "profile. It will become editable after the "
                            "challenge ends."
                        ]
            if errors:
                raise ValidationError(errors)

        # Required user fields (only when not locked)
        if not self._is_profile_fields_locked():
            for field in ["first_name", "last_name"]:
                value = attrs.get(field)
                if value is not None and (not value or not str(value).strip()):
                    errors[field] = ["This field cannot be blank."]

            # Required profile fields
            profile_data = attrs.get("profile", {})
            for field in [
                "address_street",
                "address_city",
                "address_state",
                "address_country",
                "university",
            ]:
                value = profile_data.get(field)
                if value is not None and (not value or not str(value).strip()):
                    errors[field] = ["This field cannot be blank."]

        if errors:
            raise ValidationError(errors)
        return attrs

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        fields_locked = self._is_profile_fields_locked()

        # Remove locked fields from validated_data so they keep existing values
        if fields_locked:
            for field in LOCKED_PROFILE_FIELDS:
                validated_data.pop(field, None)
                profile_data.pop(field, None)

        instance = super(ProfileSerializer, self).update(
            instance, validated_data
        )

        profile = instance.profile
        if profile_data:
            profile.affiliation = profile_data.get(
                "affiliation", profile.affiliation
            )
            profile.github_url = profile_data.get(
                "github_url", profile.github_url
            )
            profile.google_scholar_url = profile_data.get(
                "google_scholar_url", profile.google_scholar_url
            )
            profile.linkedin_url = profile_data.get(
                "linkedin_url", profile.linkedin_url
            )
            if not fields_locked:
                if profile_data.get("address_street") is not None:
                    profile.address_street = profile_data["address_street"]
                if profile_data.get("address_city") is not None:
                    profile.address_city = profile_data["address_city"]
                if profile_data.get("address_state") is not None:
                    profile.address_state = profile_data["address_state"]
                if profile_data.get("address_country") is not None:
                    profile.address_country = profile_data["address_country"]
                if profile_data.get("university") is not None:
                    profile.university = profile_data["university"]
            profile.save()
        return instance


class UserProfileSerializer(UserDetailsSerializer):
    """
    Serializer to fetch the user profile.
    """

    class Meta:
        model = Profile
        fields = (
            "affiliation",
            "github_url",
            "google_scholar_url",
            "linkedin_url",
            "address_street",
            "address_city",
            "address_state",
            "address_country",
            "university",
        )


class JwtTokenSerializer(serializers.ModelSerializer):
    """
    Serializer to update JWT token.
    """

    class Meta:
        model = JwtToken
        fields = (
            "user",
            "refresh_token",
            "access_token",
        )


class EmailBounceSerializer(serializers.ModelSerializer):
    """Serializer for updating the email_bounced flag on a Profile."""

    class Meta:
        model = Profile
        fields = ("email_bounced", "email_bounced_at")

    def clear_bounce(self):
        """Reset bounce fields after the user confirms a new email."""
        self.instance.email_bounced = False
        self.instance.email_bounced_at = None
        self.instance.save(update_fields=["email_bounced", "email_bounced_at"])
        return self.instance


class UserDeactivateSerializer(serializers.ModelSerializer):
    """Serializer for setting is_active=False on a User."""

    class Meta:
        model = get_user_model()
        fields = ("is_active",)

    def deactivate(self):
        self.instance.is_active = False
        self.instance.save(update_fields=["is_active"])
        return self.instance


class UpdateEmailSerializer(serializers.Serializer):
    """Validates a new email for the update_email endpoint."""

    email = serializers.EmailField(allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise ValidationError("Email is required.")

        user = self.context.get("user")
        if user and user.email.lower() == value:
            raise ValidationError(
                "This is already your current email address."
            )

        if (
            get_user_model()
            .objects.filter(email__iexact=value)
            .exclude(pk=user.pk)
            .exists()
        ):
            raise ValidationError("This email address is already in use.")

        from .adapter import EvalAIAccountAdapter

        adapter = EvalAIAccountAdapter()
        adapter.clean_email(value)

        return value

    def create(self, validated_data):
        user = self.context["user"]
        new_email = validated_data["email"]

        EmailAddress.objects.filter(user=user, verified=False).delete()
        email_address = EmailAddress.objects.create(
            user=user, email=new_email, primary=False, verified=False
        )
        return email_address


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """
    Serializer to check Account Active Status.
    """

    def get_email_options(self):
        try:
            user = get_user_by_email(self.data["email"])
            if not user.is_active:
                raise ValidationError(
                    {
                        "details": "Account is not active. Please contact the administrator."
                    }
                )
            else:
                return super().get_email_options()
        except User.DoesNotExist:
            raise ValidationError(
                {"details": "User with the given email does not exist."}
            )
