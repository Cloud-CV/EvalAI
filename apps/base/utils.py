from django.conf import settings

from rest_framework.pagination import PageNumberPagination


def paginated_queryset(queryset, request):
    '''
        Return a paginated result for a queryset
    '''
    paginator = PageNumberPagination()
    paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    result_page = paginator.paginate_queryset(queryset, request)
    return (paginator, result_page)
