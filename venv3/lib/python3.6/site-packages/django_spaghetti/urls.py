from django.conf.urls import url
from django.contrib import admin
from django_spaghetti.views import plate

urlpatterns = [
    url(r'^$', plate, name='plate'),
]
