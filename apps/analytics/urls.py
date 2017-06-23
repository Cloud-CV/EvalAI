from django.conf.urls import url  # noqa

from . import views

urlpatterns = [

    url(r'challenge_phase/(?P<challenge_phase_pk>[0-9]+)/submission$',
        views.get_submission_stats, name='get_submission_stats'),

]
