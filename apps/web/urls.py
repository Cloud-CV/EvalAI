from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'contact/$', views.contact_us, name='contact_us'),
    url(r'^$', views.home, name="home"),
]
