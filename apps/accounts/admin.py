from allauth.account.admin import EmailAddressAdmin as AllAuthEmailAddressAdmin
from allauth.account.models import EmailAddress
from base.admin import ImportExportTimeStampedAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ExportMixin
from rest_framework.authtoken.admin import TokenAdmin as RestTokenAdmin
from rest_framework.authtoken.models import Token

from .models import JwtToken, Profile


@admin.register(Profile)
class ProfileAdmin(ImportExportTimeStampedAdmin):
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
    class Meta:
        model = User
        fields = (
            "id",
            "date_joined",
            "email",
            "first_name",
            "last_login",
            "last_name",
            "staff_status",
            "username",
        )


class CustomUserAdmin(ExportMixin, AuthUserAdmin):
    resource_class = UserResource


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class TokenResource(resources.ModelResource):
    class Meta:
        model = Token


class CustomTokenAdmin(ExportMixin, RestTokenAdmin):
    resource_class = TokenResource
    list_filter = ("created",)
    search_fields = ("user__username",)


admin.site.unregister(Token)
admin.site.register(Token, CustomTokenAdmin)


@admin.register(JwtToken)
class JwtTokenAdmin(ImportExportTimeStampedAdmin):
    list_display = (
        "user",
        "access_token",
    )
    list_filter = ("user",)
    search_fields = ("user__username",)


class EmailAddressResource(resources.ModelResource):
    class Meta:
        model = EmailAddress


class CustomEmailAddressAdmin(ExportMixin, AllAuthEmailAddressAdmin):
    resource_class = EmailAddressResource


admin.site.unregister(EmailAddress)
admin.site.register(EmailAddress, CustomEmailAddressAdmin)
