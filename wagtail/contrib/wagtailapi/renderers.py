import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.utils.six import text_type

from rest_framework import renderers

from taggit.managers import _TaggableManager
from taggit.models import Tag

from wagtail.wagtailcore.blocks import StreamValue

from .utils import URLPath, ObjectDetailURL, get_base_url


def get_full_url(request, path):
    base_url = get_base_url(request) or ''
    return base_url + path


def find_model_detail_view(model, endpoints):
    for endpoint in endpoints:
        if endpoint.has_model(model):
            return 'wagtailapi_v1:%s:detail' % endpoint.name


class WagtailJSONRenderer(renderers.BaseRenderer):
    media_type = 'application/json'
    charset = None

    def render(self, data, media_type=None, renderer_context=None):
        request = renderer_context['request']
        endpoints = renderer_context['endpoints']

        class WagtailAPIJSONEncoder(DjangoJSONEncoder):
            def default(self, o):
                if isinstance(o, _TaggableManager):
                    return list(o.all())
                elif isinstance(o, Tag):
                    return o.name
                elif isinstance(o, URLPath):
                    return get_full_url(request, o.path)
                elif isinstance(o, ObjectDetailURL):
                    detail_view = find_model_detail_view(o.model, endpoints)

                    if detail_view:
                        return get_full_url(request, reverse(detail_view, args=(o.pk, )))
                    else:
                        return None
                elif isinstance(o, StreamValue):
                    return o.stream_block.get_prep_value(o)
                else:
                    return super(WagtailAPIJSONEncoder, self).default(o)

        ret = json.dumps(data, indent=4, cls=WagtailAPIJSONEncoder)

        # Deal with inconsistent py2/py3 behavior, and always return bytes.
        if isinstance(ret, text_type):
            return bytes(ret.encode('utf-8'))
        return ret
