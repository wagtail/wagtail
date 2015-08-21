import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.utils.six import text_type

from rest_framework import renderers

from .utils import URLPath, ObjectDetailURL, get_base_url


def get_full_url(request, path):
    base_url = get_base_url(request) or ''
    return base_url + path


def find_model_detail_view(model):
    from .endpoints import endpoints

    for endpoint in endpoints:
        if issubclass(model, endpoint.model):
            return '%s:detail' % endpoint.url_namespace


class WagtailJSONRenderer(renderers.BaseRenderer):
    media_type = 'application/json'
    charset = None

    def render(self, data, media_type=None, renderer_context=None):
        request = renderer_context['request']

        class WagtailAPIJSONEncoder(DjangoJSONEncoder):
            def default(self, o):
                if isinstance(o, URLPath):
                    return get_full_url(request, o.path)
                elif isinstance(o, ObjectDetailURL):
                    detail_view = find_model_detail_view(o.model)

                    if detail_view:
                        return get_full_url(request, reverse(detail_view, args=(o.pk, )))
                    else:
                        return None
                else:
                    return super(WagtailAPIJSONEncoder, self).default(o)

        ret = json.dumps(data, indent=4, cls=WagtailAPIJSONEncoder)

        # Deal with inconsistent py2/py3 behavior, and always return bytes.
        if isinstance(ret, text_type):
            return bytes(ret.encode('utf-8'))
        return ret
