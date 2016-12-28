from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge$', views.challenge_list,
        name='get_challenge_list'),
    url(r'challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge/(?P<pk>[0-9]+)$',
        views.challenge_detail, name='get_challenge_detail'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/participant_team/(?P<participant_team_pk>[0-9]+)',
        views.add_participant_team_to_challenge, name='add_participant_team_to_challenge'),
    url(r'challenge/(?P<pk>[0-9]+)/disable',
        views.disable_challenge, name='disable_challenge'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/challenge_phase$', views.challenge_phase_list,
        name='get_challenge_phase_list'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/(?P<pk>[0-9]+)$',
        views.challenge_phase_detail, name='get_challenge_phase_detail'),
    url(r'(?P<challenge_time>[\w.@+-]+)$', views.get_all_challenges,
        name='get_all_challenges'),
]
