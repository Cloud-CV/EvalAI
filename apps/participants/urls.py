from django.conf.urls import url
from .views import (
    ConfirmEmailView,
)

urlpatterns = [
    url(r'^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$',
        ConfirmEmailView.as_view(), name='account_confirm_email'),
]
