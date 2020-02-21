from django.conf.urls import url

from . import views
from django.conf.urls.static import static
from django.conf import Settings, settings


urlpatterns = [
    url(r"^user/disable$", views.disable_user, name="disable_user"),
    url(r"^user/get_auth_token$", views.get_auth_token, name="get_auth_token"),
    #url(r"^user/upload_avatar$", views.upload_avatar, name="upload_avatar"),
    #url(r'^user/profile_picture/$', views.profile_picture, name="profile_picture")
]# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)