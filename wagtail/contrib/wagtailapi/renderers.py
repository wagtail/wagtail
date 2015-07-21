import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse

from rest_framework import renderers

from taggit.managers import _TaggableManager
from taggit.models import Tag

from wagtail.wagtailcore.blocks import StreamValue

from .utils import URLPath, ObjectDetailURL, get_base_url


def get_full_url(request, path):
    base_url = get_base_url(request) or ''
    return base_url + path


def find_model_detail_view(model):
    from .endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint

    for endpoint in [PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint]:
        if endpoint.has_model(model):
            return 'wagtailapi_v1:%s:detail' % endpoint.name


class WagtailJSONRenderer(renderers.BaseRenderer):
    media_type = 'application/json'
    charset = None

    def render(self, data, media_type=None, renderer_context=None):
        endpoint = renderer_context['view']
        request = renderer_context['request']

        class WagtailAPIJSONEncoder(DjangoJSONEncoder):
            def default(self, o):
                if isinstance(o, _TaggableManager):
                    return list(o.all())
                elif isinstance(o, Tag):
                    return o.name
                elif isinstance(o, URLPath):
                    return get_full_url(request, o.path)
                elif isinstance(o, ObjectDetailURL):
                    view = find_model_detail_view(o.model)

                    if view:
                        return get_full_url(request, reverse(view, args=(o.pk, )))
                    else:
                        return None
                elif isinstance(o, StreamValue):
                    return o.stream_block.get_prep_value(o)
                else:
                    return super(WagtailAPIJSONEncoder, self).default(o)

        return json.dumps(data, indent=4, cls=WagtailAPIJSONEncoder)
