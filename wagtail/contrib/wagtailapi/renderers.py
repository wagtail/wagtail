import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.utils.six import text_type

from rest_framework import renderers

from .utils import ObjectDetailURL, get_full_url


def find_model_detail_view(model, endpoints):
    for endpoint in endpoints:
        if issubclass(model, endpoint.model):
            return 'wagtailapi_v1:%s:detail' % endpoint.name


class WagtailJSONRenderer(renderers.BaseRenderer):
    media_type = 'application/json'
    charset = None

    def render(self, data, media_type=None, renderer_context=None):
        request = renderer_context['request']
        endpoints = renderer_context['endpoints']

        class WagtailAPIJSONEncoder(DjangoJSONEncoder):
            def default(self, o):
                if isinstance(o, ObjectDetailURL):
                    detail_view = find_model_detail_view(o.model, endpoints)

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
