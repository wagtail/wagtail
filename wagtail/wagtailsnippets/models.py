from django.contrib.contenttypes.models import ContentType
from wagtail.wagtailadmin.utils import usage_count, used_by

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
        model.usage_count = usage_count
        model.used_by = used_by
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)
