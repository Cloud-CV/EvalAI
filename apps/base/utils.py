import os
import uuid

from django.conf import settings
from django.utils.deconstruct import deconstructible

from rest_framework.pagination import PageNumberPagination


def paginated_queryset(queryset, request):
    '''
        Return a paginated result for a queryset
    '''
    paginator = PageNumberPagination()
    paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    result_page = paginator.paginate_queryset(queryset, request)
    return (paginator, result_page)


@deconstructible
class RandomFileName(object):
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        extension = os.path.splitext(filename)[1]
        if 'id' in self.path and instance.pk:
            self.path = self.path.format(id=instance.pk)
        filename = '{}{}'.format(uuid.uuid4(), extension)
        filename = os.path.join(self.path, filename)
        return filename
