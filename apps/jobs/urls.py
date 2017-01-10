from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'challenge/(?P<challange_id>[0-9]+)/'
        r'challenge_phase/(?P<challange_phase_id>[0-9]+)/',
        views.challenge_submission, name='challenge_submission'),
]
