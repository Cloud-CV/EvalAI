from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge$', views.challenge_list,
        name='get_challenge_list'),
    url(r'challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge/(?P<pk>[0-9]+)$',
        views.challenge_detail, name='get_challenge_detail'),

]
