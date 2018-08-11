from django.conf.urls import url

from django_ses.views import dashboard


urlpatterns = [
    url(r'^$', dashboard, name='django_ses_stats'),
]
