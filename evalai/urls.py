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

from rest_framework_expiring_authtoken.views import obtain_expiring_auth_token

from accounts.views import ConfirmEmailView

urlpatterns = [url(r'^',
                   include('web.urls')),
               url(r'^',
                   include('django.contrib.auth.urls')),
               url(r'^admin/',
                   admin.site.urls),
               url(r'^api/auth/login',
                   obtain_expiring_auth_token),
               url(r'^api/auth/',
                   include('rest_auth.urls')),
               url(r'^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$',   # noqa
                   ConfirmEmailView.as_view(),
                   name='account_confirm_email'),
               url(r'^api/auth/registration/',
                   include('rest_auth.registration.urls')),
               url(r'^api/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  # noqa
                   TemplateView.as_view(
                       template_name="password_reset_confirm.html"),
                   name='password_reset_confirm'),
               url(r'^api/admin-auth/',
                   include('rest_framework.urls',
                           namespace='rest_framework')),
               url(r'^api/accounts/',
                   include('accounts.urls',
                           namespace='accounts')),
               url(r'^api/challenges/',
                   include('challenges.urls',
                           namespace='challenges')),
               url(r'^api/analytics/',
                   include('analytics.urls',
                           namespace='analytics')),
               url(r'^api/hosts/',
                   include('hosts.urls',
                           namespace='hosts')),
               url(r'^api/jobs/',
                   include('jobs.urls',
                           namespace='jobs')),
               url(r'^api/participants/',
                   include('participants.urls',
                           namespace='participants')),
               ]

# DJANGO-SPAGHETTI-AND-MEATBALLS URLs available during development only.
if settings.DEBUG:
    urlpatterns += [url(r'^dbschema/',
                    include('django_spaghetti.urls')),
                    url(r'^docs/',
                    include('rest_framework_docs.urls')),
                    ]
