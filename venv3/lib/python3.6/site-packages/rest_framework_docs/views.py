from django.http import Http404
from django.views.generic.base import TemplateView
from rest_framework_docs.api_docs import ApiDocumentation
from rest_framework_docs.settings import DRFSettings


class DRFDocsView(TemplateView):

    template_name = "rest_framework_docs/home.html"

    def get_context_data(self, **kwargs):
        settings = DRFSettings().settings
        if settings["HIDE_DOCS"]:
            raise Http404("Django Rest Framework Docs are hidden. Check your settings.")

        context = super(DRFDocsView, self).get_context_data(**kwargs)
        docs = ApiDocumentation()
        endpoints = docs.get_endpoints()

        query = self.request.GET.get("search", "")
        if query and endpoints:
            endpoints = [endpoint for endpoint in endpoints if query in endpoint.path]

        context['query'] = query
        context['endpoints'] = endpoints
        return context
