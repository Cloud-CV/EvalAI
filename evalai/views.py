from django.shortcuts import render_to_response
from django.template import RequestContext

# HTTP Error 404
def page_not_found(request):
response = render_to_response(
    'src/views/web/error/404.html',
    context_instance=RequestContext(request)
    )

    response.status_code = 404

    return response

# HTTP Error 500
def server_error(request):
response = render_to_response(
    'src/views/web/error/500.html',
    context_instance=RequestContext(request)
    )

    response.status_code = 500

    return response
