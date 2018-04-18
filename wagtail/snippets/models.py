from django.core import checks
from django.urls import reverse

from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.models import get_object_usage


SNIPPET_MODELS = []


def get_snippet_models():
    return SNIPPET_MODELS


def register_snippet(model):
    if model not in SNIPPET_MODELS:
        model.get_usage = get_object_usage
        model.get_edit_url = get_edit_url
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)

        @checks.register('panels')
        def modeladmin_model_check(app_configs, **kwargs):
            errors = check_panels_in_model(model, 'snippets')
            return errors

    return model


def get_edit_url(snippet):
    return reverse(
        'wagtailsnippets:edit',
        args=(snippet._meta.app_label, snippet._meta.model_name, snippet.pk))
