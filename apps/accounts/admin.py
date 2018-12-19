from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from import_export import resources
from import_export.admin import ExportMixin


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('date_joined', 'email', 'first_name', 'last_login', 'last_name', 'staff_status', 'username',)


class UserAdmin(ExportMixin, UserAdmin):
    resource_class = UserResource

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
