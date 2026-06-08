from django.conf.urls import url

from . import views


app_name = "scout"

urlpatterns = [
    url(
        r"^webhook/(?P<name>[^/]+)/(?P<token>[^/]+)/$",
        views.webhook_receiver,
        name="webhook",
    ),
]
