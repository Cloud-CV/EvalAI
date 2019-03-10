from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^user/disable$", views.disable_user, name="disable_user"),
    url(r"^user/get_auth_token$", views.get_auth_token, name="get_auth_token"),
    url(
        r"^challenge/invitation/(?P<challenge_pk>[0-9]+)/$",
        views.invite_users_to_challenge,
        name="invite_users_to_challenge",
    ),
    url(
        r"^accept/invitation/(?P<invitation_key>[\w-]+)/$",
        views.accept_challenge_invitation,
        name="accept_challenge_invitation",
    ),
]
