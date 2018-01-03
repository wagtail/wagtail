from django.core.checks import register

from wagtail.admin.checks import check_panel_config


@register()
def snippets_panels_check(app_configs, **kwargs):
    from wagtail.snippets.models import get_snippet_models

    errors = []

    for snippet_model in get_snippet_models():
        errors += check_panel_config(snippet_model, 'snippet')

    return errors
