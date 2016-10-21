from django.conf import settings
from storages.backends.s3boto import S3BotoStorage

# In order to make sure that both static and media files are stored in different directories

class StaticStorage(S3BotoStorage):
    location = settings.STATICFILES_LOCATION

class MediaStorage(S3BotoStorage):
    location = settings.MEDIAFILES_LOCATION
