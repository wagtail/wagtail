from django.contrib.admin.utils import quote
from django.core import checks
from django.urls import reverse

from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.utils import get_object_usage

SNIPPET_MODELS = []


def get_snippet_models():
    return SNIPPET_MODELS


def register_snippet(model):
    if model not in SNIPPET_MODELS:
        model.get_usage = get_object_usage
        model.usage_url = get_snippet_usage_url
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)

        @checks.register('panels')
        def modeladmin_model_check(app_configs, **kwargs):
            errors = check_panels_in_model(model, 'snippets')
            return errors

    return model


def get_snippet_usage_url(self):
    return reverse('wagtailsnippets:usage', args=(
        self._meta.app_label, self._meta.model_name, quote(self.pk)))
