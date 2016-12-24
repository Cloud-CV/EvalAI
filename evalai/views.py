from django.shortcuts import render_to_response
from django.template import RequestContext


def page_not_found(request):
    response = render_to_response('src/views/web/error/404.html',
                                  context_instance=RequestContext(request)
                                  )
    response.status_code = 404
    return response


def server_error(request):
    response = render_to_response('src/views/web/error/500.html',
                                  context_instance=RequestContext(request)
                                  )
    response.status_code = 500
    return response
