from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'challenge/(?P<challenge_id>[0-9]+)/'
        r'challenge_phase/(?P<challenge_phase_id>[0-9]+)/submission/',
        views.challenge_submission, name='challenge_submission'),
    url(r'get_challenge/(?P<challenge_id>[0-9]+)/'
        r'get_challenge_phase/(?P<challenge_phase_id>[0-9]+)/submission/',
        views.get_challenge_submission, name='get_challenge_submission'),
]
