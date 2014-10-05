from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from wagtail.wagtailadmin.utils import get_object_usage

SNIPPET_MODELS = []

SNIPPET_CONTENT_TYPES = None


def get_snippet_content_types():
    global SNIPPET_CONTENT_TYPES
    if SNIPPET_CONTENT_TYPES is None:
        SNIPPET_CONTENT_TYPES = [
            ContentType.objects.get_for_model(model)
            for model in SNIPPET_MODELS
        ]

    return SNIPPET_CONTENT_TYPES


def register_snippet(model):
    if model not in SNIPPET_MODELS:
        model.get_usage = get_object_usage
        model.usage_url = get_snippet_usage_url
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)
    return model


def get_snippet_usage_url(self):
    content_type = ContentType.objects.get_for_model(self)
    return reverse('wagtailsnippets_usage',
                   args=(content_type.app_label,
                         content_type.model,
                         self.id,))
