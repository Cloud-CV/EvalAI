from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge$', views.challenge_list,
        name='get_challenge_list'),
    url(r'challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/challenge/(?P<challenge_pk>[0-9]+)$',
        views.challenge_detail, name='get_challenge_detail'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/participant_team/(?P<participant_team_pk>[0-9]+)',
        views.add_participant_team_to_challenge, name='add_participant_team_to_challenge'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/disable',
        views.disable_challenge, name='disable_challenge'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/challenge_phase$', views.challenge_phase_list,
        name='get_challenge_phase_list'),
    url(r'challenge/(?P<challenge_pk>[0-9]+)/challenge_phase/(?P<pk>[0-9]+)$',
        views.challenge_phase_detail, name='get_challenge_phase_detail'),
    # `A-Za-z` because it accepts either of `all, future, past or present` in either case
    url(r'challenge/(?P<challenge_time>[A-Za-z]+)$', views.get_all_challenges,
        name='get_all_challenges'),
    url(r'challenge/(?P<pk>[0-9]+)/',
        views.get_challenge_by_pk, name='get_challenge_by_pk'),
    url(r'challenge$', views.get_challenges_based_on_teams,
        name='get_challenges_based_on_teams'),
    url(r'(?P<challenge_pk>[0-9]+)/challenge_phase_split$', views.challenge_phase_split_list,
        name='challenge_phase_split_list'),
    url(r'challenge/challenge_host_team/(?P<challenge_host_team_pk>[0-9]+)/zip_upload/$',
        views.create_challenge_using_zip_file,
        name='create_challenge_using_zip_file'),
    url(r'(?P<challenge_pk>[0-9]+)/challenge_phase/(?P<challenge_phase_pk>[0-9]+)/submissions$',
        views.get_all_submissions_of_challenge,
        name='get_all_submissions_of_challenge'),
    url(r'(?P<challenge_pk>[0-9]+)/download_all_submissions_file/(?P<file_type>[A-Za-z]+)/$',
        views.download_all_submissions_file,
        name='download_all_submissions_file')
]
