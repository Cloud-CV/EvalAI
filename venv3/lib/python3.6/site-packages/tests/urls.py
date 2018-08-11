from __future__ import absolute_import, division, print_function

from django.conf.urls import include, url
from django.contrib import admin
from tests import views

accounts_urls = [
    url(r'^login/$', views.LoginView.as_view(), name="login"),
    url(r'^login2/$', views.LoginWithSerilaizerClassView.as_view(), name="login2"),
    url(r'^register/$', views.UserRegistrationView.as_view(), name="register"),
    url(r'^reset-password/$', view=views.PasswordResetView.as_view(), name="reset-password"),
    url(r'^reset-password/confirm/$', views.PasswordResetConfirmView.as_view(), name="reset-password-confirm"),

    url(r'^user/profile/$', views.UserProfileView.as_view(), name="profile"),

    url(r'^test/$', views.TestView.as_view(), name="test-view"),
]

organisations_urls = [
    url(r'^create/$', view=views.CreateOrganisationView.as_view(), name="create"),
    url(r'^(?P<slug>[\w-]+)/members/$', view=views.OrganisationMembersView.as_view(), name="members"),
    url(r'^(?P<slug>[\w-]+)/leave/$', view=views.LeaveOrganisationView.as_view(), name="leave"),
    url(r'^(?P<slug>[\w-]+)/errored/$', view=views.OrganisationErroredView.as_view(), name="errored")
]

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_docs.urls')),

    # API
    url(r'^accounts/', view=include(accounts_urls, namespace='accounts')),
    url(r'^organisations/', view=include(organisations_urls, namespace='organisations')),

    # Endpoints without parents/namespaces
    url(r'^another-login/$', views.LoginView.as_view(), name="login"),
]
