from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^user/disable$', views.disable_user, name='disable_user'),
    url(r'^user/get_auth_token$', views.get_auth_token, name='get_auth_token'),
    url(r'^user/new_auth_token$', views.new_auth_token, name='new_auth_token'),
]
