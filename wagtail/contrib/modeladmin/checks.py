from django.core import checks


@checks.register('panels')
def modeladmin_model_panels_check(app_configs, **kwargs):
    """Checks panels configuration in all models used within modeladmin."""
    from wagtail.admin.checks import check_panels_in_model
    from .options import get_modeladmin_models

    errors = []

    for model in get_modeladmin_models():
        errors.extend(check_panels_in_model(model, context='modeladmin'))

    return errors
