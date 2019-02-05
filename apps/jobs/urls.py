from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^challenge/(?P<challenge_pk>[0-9]+)/'
        r'challenge_phase/(?P<challenge_phase_pk>[0-9]+)/submission/(?P<submission_pk>[0-9]+)$',
        views.change_submission_data_and_visibility, name='change_submission_data_and_visibility'),
    url(r'^challenge/(?P<challenge_id>[0-9]+)/'
        r'challenge_phase/(?P<challenge_phase_id>[0-9]+)/submission/$',
        views.challenge_submission, name='challenge_submission'),
    url(r'^(?P<challenge_pk>[0-9]+)/'
        r'phases/(?P<challenge_phase_pk>[0-9]+)/'
        r'remaining_submissions$',
        views.get_remaining_submissions, name='get_remaining_submissions'),
    url(r'^challenge_phase_split/(?P<challenge_phase_split_id>[0-9]+)/leaderboard/$',
        views.leaderboard, name='leaderboard'),
    url(r'^submission/(?P<submission_id>[0-9]+)$',
        views.get_submission_by_pk, name='get_submission_by_pk'),
    url(r'^challenge/(?P<challenge_pk>[0-9]+)/submission/(?P<submission_pk>[0-9]+)/queue/(?P<queue_name>[\w-]+)/$',
        views.update_submission_status_by_queue_name, name='update_submission_status_by_queue_name'),
    url(r'^submission/(?P<submission_pk>[0-9]+)/queue/(?P<queue_name>[\w-]+)/$',
        views.get_submission_by_pk_using_queue_name, name='get_submission_by_pk_using_queue_name'),
    url(r'^v1/challenge/(?P<challenge_pk>[0-9]+)/update_submission/queue/(?P<queue_name>[\w-]+)/$',
        views.update_submission_by_queue_name, name='update_submission_by_queue_name'),
    url(r'^challenge/(?P<challenge_pk>[0-9]+)/update_submission/$',
        views.update_submission, name='update_submission'),
    url(r'^challenge/queue/(?P<queue_name>[\w-]+)/receipt/(?P<receipt_handle>[\w-]+)$',
        views.delete_submission_message_by_queue_name, name='delete_submission_message_by_queue_name'),
    url(r'^challenge/(?P<challenge_pk>[0-9]+)/queue/(?P<queue_name>[\w-]+)/$',
        views.get_submission_message_by_queue_name, name='get_submission_message_by_queue_name'),
]
