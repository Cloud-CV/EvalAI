from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'challenge/(?P<challenge_id>[0-9]+)/'
        r'challenge_phase/(?P<challenge_phase_id>[0-9]+)/submission/',
        views.challenge_submission, name='challenge_submission'),
    url(r'challenge/(?P<challenge_id>[0-9]+)/'
        r'challenge_phase/(?P<challenge_phase_id>[0-9]+)/leaderboard/',
        views.leaderboard, name='leaderboard'),
]
