from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'challenge/(?P<challenge_pk>[0-9]+)/participant$', views.participant_team_list,
        name='get_participant_team_list'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/participant/(?P<pk>[0-9]+)$', views.participant_team_detail,
        name='get_participant_team_details'),
]
