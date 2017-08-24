from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'challenge/(?P<challenge_pk>[0-9]+)/team/count$',
        views.get_participant_team_count, name='get_participant_team_count'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/participant/count$',
        views.get_participant_count, name='get_participant_count'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/submission/(?P<duration>[A-Za-z]+)/count$',
        views.get_submission_count, name='get_submission_count'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/(?P<challenge_phase_pk>[0-9]+)/count$',
        views.get_challenge_phase_submission_analysis, name='get_challenge_phase_submission_analysis'),
]
