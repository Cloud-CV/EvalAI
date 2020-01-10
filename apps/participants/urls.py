from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^participant_team/(?P<pk>[0-9]+)/invite$",
        views.invite_participant_to_team,
        name="invite_participant_to_team",
    ),
    url(
        r"^participant_team/(?P<participant_team_pk>[0-9]+)/challenge$",
        views.get_participant_team_challenge_list,
        name="get_participant_team_challenge_list",
    ),
    url(
        r"^remove_self_from_participant_team/(?P<participant_team_pk>[0-9]+)$",
        views.remove_self_from_participant_team,
        name="remove_self_from_participant_team",
    ),
    url(
        r"^participant_team/(?P<participant_team_pk>[0-9]+)/participant/(?P<participant_pk>[0-9]+)$",
        views.delete_participant_from_team,
        name="delete_participant_from_team",
    ),
    url(
        r"^participant_teams/challenges/(?P<challenge_pk>[0-9]+)/user$",
        views.get_teams_and_corresponding_challenges_for_a_participant,
        name="get_teams_and_corresponding_challenges_for_a_participant",
    ),
    url(
        r"^participant_team$",
        views.participant_team_list,
        name="get_participant_team_list",
    ),
    url(
        r"^participant_team/(?P<pk>[0-9]+)$",
        views.participant_team_detail,
        name="get_participant_team_details",
    ),
]
