from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^challenge_host_team/$",
        views.challenge_host_team_list,
        name="get_challenge_host_team_list",
    ),
    url(
        r"^challenge_host_team/(?P<pk>[0-9]+)$",
        views.challenge_host_team_detail,
        name="get_challenge_host_team_details",
    ),
    url(
        r"^create_challenge_host_team$",
        views.create_challenge_host_team,
        name="create_challenge_host_team",
    ),
    url(
        r"^challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge_host$",
        views.challenge_host_list,
        name="get_challenge_host_list",
    ),
    url(
        r"^challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge_host/(?P<pk>[0-9]+)$",
        views.challenge_host_detail,
        name="get_challenge_host_details",
    ),
    url(
        r"^remove_self_from_challenge_host/(?P<challenge_host_team_pk>[0-9]+)$",
        views.remove_self_from_challenge_host_team,
        name="remove_self_from_challenge_host_team",
    ),
    url(
        r"^challenge_host_teams/(?P<pk>[0-9]+)/invite$",
        views.invite_host_to_team,
        name="invite_host_to_team",
    ),
]
