"""Admin configuration for user-related models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress
from allauth.account.admin import EmailAddressAdmin as AllauthEmailAddressAdmin

from import_export import resources
from import_export.admin import ExportMixin
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin as DRFTokenAdmin

from base.admin import ImportExportTimeStampedAdmin
from .models import Profile, JwtToken


@admin.register(Profile)
class ProfileAdmin(ImportExportTimeStampedAdmin):
    """Admin view for the Profile model."""

    list_display = (
        "id",
        "user",
        "contact_number",
        "affiliation",
        "receive_participated_challenge_updates",
        "recieve_newsletter",
        "github_url",
        "google_scholar_url",
        "linkedin_url",
    )
    list_filter = (
        "receive_participated_challenge_updates",
        "recieve_newsletter",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "contact_number",
        "github_url",
        "google_scholar_url",
        "linkedin_url",
    )


class UserResource(resources.ModelResource):
    """Resource class for exporting User model data."""

    class Meta:
        model = User
        fields = (
            "id",
            "date_joined",
            "email",
            "first_name",
            "last_login",
            "last_name",
            "is_staff",
            "username",
        )


class CustomUserAdmin(ExportMixin, DjangoUserAdmin):
    """Customized User admin with export functionality."""

    resource_class = UserResource


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class TokenResource(resources.ModelResource):
    """Resource class for exporting DRF Token model data."""

    class Meta:
        model = Token


class CustomTokenAdmin(DRFTokenAdmin):
    """Customized Token admin with export and filtering."""

    resource_class = TokenResource
    list_filter = ("created",)
    search_fields = ("user__username",)


admin.site.unregister(Token)
admin.site.register(Token, CustomTokenAdmin)


@admin.register(JwtToken)
class JwtTokenAdmin(ImportExportTimeStampedAdmin):
    """Admin view for JwtToken model."""

    list_display = (
        "user",
        "access_token",
    )
    list_filter = ("user",)
    search_fields = ("user__username",)


class EmailAddressResource(resources.ModelResource):
    """Resource class for exporting EmailAddress model data."""

    class Meta:
        model = EmailAddress


class CustomEmailAddressAdmin(ExportMixin, AllauthEmailAddressAdmin):
    """Customized EmailAddress admin with export functionality."""

    resource_class = EmailAddressResource


admin.site.unregister(EmailAddress)
admin.site.register(EmailAddress, CustomEmailAddressAdmin)
