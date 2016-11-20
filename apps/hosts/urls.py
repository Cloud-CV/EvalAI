from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'challenge_host_team/$', views.challenge_host_team_list, name='get_challenge_host_team_list'),

]
