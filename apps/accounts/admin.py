from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from import_export import resources
from import_export.admin import ExportMixin
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import Token


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'date_joined', 'email', 'first_name', 'last_login', 'last_name', 'staff_status', 'username',)


class UserAdmin(ExportMixin, UserAdmin):
    resource_class = UserResource

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class TokenResource(resources.ModelResource):
    class Meta:
        model = Token


class TokenAdmin(TokenAdmin):
    resource_class = TokenResource
    list_filter = ('created',)
    search_fields = ('user__username',)

admin.site.unregister(Token)
admin.site.register(Token, TokenAdmin)
