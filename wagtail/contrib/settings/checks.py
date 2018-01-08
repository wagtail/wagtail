from django.core.checks import register

from wagtail.admin.checks import check_panel_config


@register()
def settings_panels_check(app_configs, **kwargs):
    """Checks all settings models for correct `panels` configuration."""
    from wagtail.contrib.settings.registry import registry

    errors = []

    for settings_model in registry:
        errors += check_panel_config(settings_model, 'wagtailsettings')

    return errors
