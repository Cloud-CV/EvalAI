from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'challenge/(?P<challenge_pk>[0-9]+)/team/count$',
        views.get_participant_team_count, name='get_participant_team_count'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/participant/count$',
        views.get_participant_count, name='get_participant_count'),

]
