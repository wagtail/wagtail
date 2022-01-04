import django

# Imported for historical reasons
from wagtail import __semver__, __version__  # noqa


if django.VERSION >= (3, 2):
    # The declaration is only needed for older Django versions
    pass
else:
    default_app_config = 'wagtail.core.apps.WagtailCoreAppConfig'


def setup():
    import warnings

    from wagtail.utils.deprecation import removed_in_next_version_warning

    warnings.simplefilter("default", removed_in_next_version_warning)


setup()
