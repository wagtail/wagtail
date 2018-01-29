from django.core import checks


@checks.register('panels')
def settings_model_panels_check(app_configs, **kwargs):
    """Checks panels configuration in all settings models."""
    from wagtail.admin.checks import check_panels_in_model
    from .registry import registry

    errors = []

    for model in registry:
        errors.extend(check_panels_in_model(model, context='settings'))

    return errors
