from django.urls import reverse

SNIPPET_MODELS = []


def get_snippet_models():
    return SNIPPET_MODELS


def register_snippet(model):
    if model not in SNIPPET_MODELS:
        model.get_edit_url = get_edit_url
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)
    return model


def get_edit_url(snippet):
    return reverse(
        'wagtailsnippets:edit',
        args=(snippet._meta.app_label, snippet._meta.model_name, snippet.pk))
