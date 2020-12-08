from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/team/count$",
        views.get_participant_team_count,
        name="get_participant_team_count",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/participant/count$",
        views.get_participant_count,
        name="get_participant_count",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/submission/(?P<duration>[A-Za-z]+)/count$",
        views.get_submission_count,
        name="get_submission_count",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/(?P<challenge_phase_pk>[0-9]+)/analytics$",
        views.get_challenge_phase_submission_analysis,
        name="get_challenge_phase_submission_analysis",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/(?P<challenge_phase_pk>[0-9]+)/count$",
        views.get_challenge_phase_submission_count_by_team,
        name="get_challenge_phase_submission_count_by_team",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/"
        r"(?P<challenge_phase_pk>[0-9]+)/last_submission/(?P<submission_by>[A-Za-z_]+)$",
        views.get_last_submission_time,
        name="get_last_submission_time",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/"
        r"(?P<challenge_phase_pk>[0-9]+)/last_submission_datetime_analysis/$",
        views.get_last_submission_datetime_analysis,
        name="get_last_submission_datetime_analysis",
    ),
    url(
        r"^challenges/(?P<challenge_pk>[0-9]+)/download_all_participants/$",
        views.download_all_participants,
        name="download_all_participants",
    ),
]

app_name = "analytics"
