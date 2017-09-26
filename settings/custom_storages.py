from storages.backends.s3boto import S3BotoStorage

from .prod import STATICFILES_LOCATION, MEDIAFILES_LOCATION

# In order to make sure that both static and media files are stored in
# different directories


class StaticStorage(S3BotoStorage):
    location = STATICFILES_LOCATION


class MediaStorage(S3BotoStorage):
    location = MEDIAFILES_LOCATION
