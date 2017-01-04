from django.shortcuts import render
from django.template import RequestContext


def page_not_found(request):
    response = render(request, 'src/views/web/error-pages/error-404.html',
                      )
    response.status_code = 404
    return response


def internal_server_error(request):
    response = render(request, 'src/views/web/error-pages/error-500.html',
                      )
    response.status_code = 500
    return response
