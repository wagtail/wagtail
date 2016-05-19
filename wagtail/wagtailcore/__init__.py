__version__ = '1.4.5'
# Required for npm package for frontend
__semver__ = '1.4.5'
default_app_config = 'wagtail.wagtailcore.apps.WagtailCoreAppConfig'


def setup():
    import warnings
    from wagtail.utils.deprecation import removed_in_next_version_warning

    warnings.simplefilter("default", removed_in_next_version_warning)

setup()
