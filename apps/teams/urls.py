from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.team_list, name='get_team_list'),
    url(r'(?P<pk>[0-9]+)$', views.team_detail, name='get_team_details'),
    url(r'^documents/$', views.schema_view, name='schema_view'),
]
