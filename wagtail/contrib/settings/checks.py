from django.core.checks import register

from wagtail.admin.checks import check_panel_config


@register()
def settings_panels_check(app_configs, **kwargs):
    from wagtail.contrib.settings import registry

    errors = []
    print('does this do anything')

    for settings_model in registry:
        errors += check_panel_config(settings_model, 'wagtailsettings')

    return errors
