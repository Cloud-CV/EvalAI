from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^user/disable$', views.disable_user, name='disable_user'),
    url(r'^user/resend-email$', views.resend_email, name='resend_email'),
]
