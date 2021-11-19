import django


if django.VERSION >= (3, 2):
    # The declaration is only needed for older Django versions
    pass
else:
    default_app_config = 'wagtail.sites.apps.WagtailSitesAppConfig'
