import os
import uuid

from django.conf import settings
from django.utils.deconstruct import deconstructible

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination


class StandardResultSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


def paginated_queryset(queryset, request, pagination_class=PageNumberPagination()):
    '''
        Return a paginated result for a queryset
    '''
    paginator = pagination_class
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
        elif 'id' not in self.path and instance.pk:
            path = "submission_files/submission_{id}"
            self.path = path.format(id=instance.pk)
        filename = '{}{}'.format(uuid.uuid4(), extension)
        filename = os.path.join(self.path, filename)
        return filename


def get_model_object(model_name):
    def get_model_by_pk(pk):
        try:
            model_object = model_name.objects.get(pk=pk)
            return model_object
        except model_name.DoesNotExist:
            raise NotFound('{} {} does not exist'.format(model_name.__name__, pk))
    get_model_by_pk.__name__ = 'get_{}_object'.format(model_name.__name__.lower())
    return get_model_by_pk
