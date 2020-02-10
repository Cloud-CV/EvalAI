from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/"
        r"challenge_phase/(?P<challenge_phase_pk>[0-9]+)/submission/(?P<submission_pk>[0-9]+)$",
        views.change_submission_data_and_visibility,
        name="change_submission_data_and_visibility",
    ),
    url(
        r"^challenge/(?P<challenge_id>[0-9]+)/"
        r"challenge_phase/(?P<challenge_phase_id>[0-9]+)/submission/$",
        views.challenge_submission,
        name="challenge_submission",
    ),
    url(
        r"^(?P<challenge_pk>[0-9]+)/" r"remaining_submissions/$",
        views.get_remaining_submissions,
        name="get_remaining_submissions",
    ),
    url(
        r"^submissions/(?P<submission_pk>[0-9]+)/re-run/$",
        views.re_run_submission,
        name="re_run_submission",
    ),
    url(
        r"^challenge_phase_split/(?P<challenge_phase_split_id>[0-9]+)/leaderboard/$",
        views.leaderboard,
        name="leaderboard",
    ),
    url(
        r"^submission/(?P<submission_id>[0-9]+)$",
        views.get_submission_by_pk,
        name="get_submission_by_pk",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/update_submission/$",
        views.update_submission,
        name="update_submission",
    ),
    url(
        r"^challenge/(?P<challenge_pk>[0-9]+)/submission/",
        views.get_submissions_for_challenge,
        name="get_submissions_for_challenge",
    ),
    url(
        r"^queues/(?P<queue_name>[\w-]+)/$",
        views.delete_submission_message_from_queue,
        name="delete_submission_message_from_queue",
    ),
    url(
        r"^challenge/queues/(?P<queue_name>[\w-]+)/$",
        views.get_submission_message_from_queue,
        name="get_submission_message_from_queue",
    ),
    url(
        r"^submission_files/$",
        views.get_signed_url_for_submission_related_file,
        name="get_signed_url_for_submission_related_file",
    ),
    url(
        r"^leaderboard_data/(?P<leaderboard_data_pk>[0-9]+)/$",
        views.update_leaderboard_data,
        name="update_leaderboard_data",
    ),
]
