from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^user/disable$", views.disable_user, name="disable_user"),
    url(r"^user/generate_activation_link/(?P<user_email>[\w.@+-]+)/$",
        views.generate_activation_link,
        name="generate_activation_link"
        ),
    url(r"^user/activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$",
        views.activate_user,
        name="activate_user"
        ),
    url(r"^user/get_auth_token$", views.get_auth_token, name="get_auth_token"),
    url(
        r"^user/refresh_auth_token$",
        views.refresh_auth_token,
        name="refresh_auth_token",
    ),
    url(
        r"^user/resend_email_verification/$",
        views.resend_email_confirmation,
        name="resend_email_confirmation",
    ),
]

app_name = "accounts"
