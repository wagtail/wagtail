from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from wagtail.wagtailadmin.utils import get_object_usage

SNIPPET_MODELS = []


def get_snippet_models():
    return SNIPPET_MODELS


def register_snippet(model):
    if model not in SNIPPET_MODELS:
        model.get_usage = get_object_usage
        model.usage_url = get_snippet_usage_url
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)
    return model


def get_snippet_usage_url(self):
    return reverse('wagtailsnippets:usage', args=(
        self._meta.app_label, self._meta.model_name, self.id))
