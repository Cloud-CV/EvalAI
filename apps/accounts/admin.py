from allauth.account.admin import EmailAddressAdmin
from allauth.account.models import EmailAddress
from base.admin import ImportExportTimeStampedAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ExportMixin
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

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


class UserAdmin(ExportMixin, UserAdmin):
    resource_class = UserResource


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class TokenResource(resources.ModelResource):
    class Meta:
        model = Token


class TokenAdmin(TokenAdmin):
    resource_class = TokenResource
    list_filter = ("created",)
    search_fields = ("user__username",)


admin.site.unregister(Token)
admin.site.register(Token, TokenAdmin)


def _get_outstanding_token_for_jwt(jwt_token):
    if jwt_token.refresh_token:
        outstanding_token = OutstandingToken.objects.filter(
            token=jwt_token.refresh_token
        ).first()
        if outstanding_token is not None:
            return outstanding_token

    return (
        OutstandingToken.objects.filter(user=jwt_token.user)
        .order_by("-created_at")
        .first()
    )


@admin.register(JwtToken)
class JwtTokenAdmin(ImportExportTimeStampedAdmin):
    exclude = ()
    list_display = (
        "user",
        "created_at",
        "modified_at",
        "jwt_issued_at",
        "jwt_expires_at",
        "is_blacklisted",
    )
    list_filter = ("user",)
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "user",
        "access_token",
        "refresh_token",
        "created_at",
        "modified_at",
        "jwt_issued_at",
        "jwt_expires_at",
        "is_blacklisted",
    )

    def jwt_issued_at(self, obj):
        outstanding_token = _get_outstanding_token_for_jwt(obj)
        if outstanding_token is None:
            return "-"
        return outstanding_token.created_at

    jwt_issued_at.short_description = "JWT issued at"
    jwt_issued_at.admin_order_field = "modified_at"

    def jwt_expires_at(self, obj):
        outstanding_token = _get_outstanding_token_for_jwt(obj)
        if outstanding_token is None:
            return "-"
        return outstanding_token.expires_at

    jwt_expires_at.short_description = "JWT expires at"

    def is_blacklisted(self, obj):
        outstanding_token = _get_outstanding_token_for_jwt(obj)
        if outstanding_token is None:
            return None
        return BlacklistedToken.objects.filter(
            token=outstanding_token
        ).exists()

    is_blacklisted.short_description = "Blacklisted"
    is_blacklisted.boolean = True


admin.site.unregister(JwtToken)
admin.site.register(JwtToken, JwtTokenAdmin)


class EmailAddressResource(resources.ModelResource):
    class Meta:
        model = EmailAddress


class EmailAddressAdmin(ExportMixin, EmailAddressAdmin):
    resource_class = EmailAddressResource


admin.site.unregister(EmailAddress)
admin.site.register(EmailAddress, EmailAddressAdmin)
