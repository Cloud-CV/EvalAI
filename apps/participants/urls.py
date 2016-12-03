from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'participant_team$', views.participant_team_list, name='get_participant_team_list'),
    url(r'participant_team/(?P<pk>[0-9]+)$', views.participant_team_detail, name='get_participant_team_details'),
    url(r'participant_team/(?P<pk>[0-9]+)/invite$', views.invite_participant_to_team,
        name='invite_participant_to_team'),
]
