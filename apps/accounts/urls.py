from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^user/disable$", views.disable_user, name="disable_user"),
    url(r"^user/get_auth_token$", views.get_auth_token, name="get_auth_token"),
]
