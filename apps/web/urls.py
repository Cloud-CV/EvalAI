from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^contact/$", views.contact_us, name="contact_us"),
    url(r"^team/$", views.our_team, name="our_team"),
    url(
        r"^notify_users/$",
        views.notify_users_about_challenge,
        name="notify_users_about_challenge",
    ),
]
