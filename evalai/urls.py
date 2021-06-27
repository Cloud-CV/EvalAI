"""evalai URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from allauth.account.views import ConfirmEmailView
from rest_framework_expiring_authtoken.views import obtain_expiring_auth_token
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from web import views

handler404 = "web.views.page_not_found"
handler500 = "web.views.internal_server_error"

swagger_api_info = openapi.Info(
    title="EvalAI API",
    default_version="v1",
    description="EvalAI Documentation",
    contact=openapi.Contact(email="team@cloudcv.org"),
    license=openapi.License(name="BSD License"),
)

schema_view = get_schema_view(
    public=True, permission_classes=(permissions.AllowAny,)
)

urlpatterns = [
    url(r"^$", views.home, name="home"),
    url(r"^api/allauth/accounts/", include("allauth.urls")),
    url(r"^api/admin/", admin.site.urls),
    url(
        r"^api/auth/login",
        obtain_expiring_auth_token,
        name="obtain_expiring_auth_token",
    ),
    url(r"^api/auth/", include("rest_auth.urls")),
    url(
        r"^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$",  # noqa
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    url(r"^api/auth/registration/", include("rest_auth.registration.urls")),
    url(
        r"^auth/api/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$",  # noqa
        TemplateView.as_view(template_name="password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    url(
        r"^api/auth/email-confirmed/$",
        TemplateView.as_view(template_name="account/email_confirm.html"),
        name="email_confirm_done",
    ),
    url(r"^api/accounts/", include("accounts.urls", namespace="accounts")),
    url(
        r"^api/challenges/", include("challenges.urls", namespace="challenges")
    ),
    url(r"^api/analytics/", include("analytics.urls", namespace="analytics")),
    url(r"^api/hosts/", include("hosts.urls", namespace="hosts")),
    url(r"^api/jobs/", include("jobs.urls", namespace="jobs")),
    url(
        r"^api/participants/",
        include("participants.urls", namespace="participants"),
    ),
    url(r"^api/web/", include("web.urls", namespace="web")),
    url(r"^email_reporting/", include("django_ses.urls")),
    url(
        r"^api/docs/docs(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-yaml",
    ),
    url(
        r"^api/docs/$",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    url(r"^api/prometheus/", include("django_prometheus.urls")),
]

# DJANGO-SPAGHETTI-AND-MEATBALLS URLs available during development only.
if settings.DEBUG:
    urlpatterns += (
        [
            url(r"^dbschema/", include("django_spaghetti.urls")),
            url(
                r"^api/admin-auth/",
                include("rest_framework.urls", namespace="rest_framework"),
            ),
            url(r"^silk/", include("silk.urls", namespace="silk")),
        ]
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    )
