from django.urls import path

from . import views

urlpatterns = [
    path(
        "challenge_host_team",
        views.get_all_challenge_host_teams,
        name="get_all_challenge_host_teams",
    ),
    path(
        "challenge_host_team/<int:pk>",
        views.get_challenge_host_team,
        name="get_challenge_host_team",
    ),
    path(
        "challenge_host_team/<int:pk>/disable",
        views.disable_challenge_host_team,
        name="disable_challenge_host_team",
    ),
    path(
        "challenge_host_team/<int:pk>/delete",
        views.delete_challenge_host_team,
        name="delete_challenge_host_team",
    ),
    path(
        "challenge_host_team/<int:pk>/edit",
        views.edit_challenge_host_team,
        name="edit_challenge_host_team",
    ),
    path(
        "challenge_host_team/<int:pk>/accept_invite/<int:user_pk>",
        views.accept_invite,
        name="accept_invite",
    ),
    path(
        "challenge_host_teams/<int:pk>/invite",
        views.invite_host_to_team,
        name="invite_host_to_team",
    ),
]
