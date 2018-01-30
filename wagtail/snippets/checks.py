from django.core.checks import register


@register('panels')
def snippet_model_panels_check(app_configs, **kwargs):
    from wagtail.admin.checks import check_panels_in_model
    from wagtail.snippets.models import get_snippet_models

    errors = []

    for snippet_model in get_snippet_models():
        errors += check_panels_in_model(snippet_model, 'snippet')

    return errors
