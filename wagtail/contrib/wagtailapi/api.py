import json
from functools import wraps

from django.conf.urls import url, include
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse

from taggit.managers import _TaggableManager
from taggit.models import Tag

from wagtail.utils.urlpatterns import decorate_urlpatterns

from .endpoints import URLPath, ObjectDetailURL, PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint
from .utils import BadRequestError, get_base_url


def get_full_url(request, path):
    base_url = get_base_url(request) or ''
    return base_url + path


class API(object):
    def __init__(self, endpoints):
        self.endpoints = endpoints

    def find_model_detail_view(self, model):
        for endpoint_name, endpoint in self.endpoints.items():
            if endpoint.has_model(model):
                return 'wagtailapi_v1:%s:detail' % endpoint_name

    def make_response(self, request, data, response_cls=HttpResponse):
        api = self

        class WagtailAPIJSONEncoder(DjangoJSONEncoder):
            def default(self, o):
                if isinstance(o, _TaggableManager):
                    return list(o.all())
                elif isinstance(o, Tag):
                    return o.name
                elif isinstance(o, URLPath):
                    return get_full_url(request, o.path)
                elif isinstance(o, ObjectDetailURL):
                    view = api.find_model_detail_view(o.model)

                    if view:
                        return get_full_url(request, reverse(view, args=(o.pk, )))
                    else:
                        return None
                else:
                    return super(WagtailAPIJSONEncoder, self).default(o)

        return response_cls(
            json.dumps(data, indent=4, cls=WagtailAPIJSONEncoder),
            content_type='application/json'
        )

    def api_view(self, view):
        """
        This is a decorator that is applied to all API views.

        It is responsible for serialising the responses from the endpoints
        and handling errors.
        """
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            # Catch exceptions and format them as JSON documents
            try:
                return self.make_response(request, view(request, *args, **kwargs))
            except Http404 as e:
                return self.make_response(request, {
                    'message': str(e)
                }, response_cls=HttpResponseNotFound)
            except BadRequestError as e:
                return self.make_response(request, {
                    'message': str(e)
                }, response_cls=HttpResponseBadRequest)

        return wrapper

    def get_urlpatterns(self):
        return decorate_urlpatterns([
            url(r'^%s/' % name, include(endpoint.get_urlpatterns(), namespace=name))
            for name, endpoint in self.endpoints.items()
        ], self.api_view)


v1 = API({
    'pages': PagesAPIEndpoint(),
    'images': ImagesAPIEndpoint(),
    'documents': DocumentsAPIEndpoint(),
})
