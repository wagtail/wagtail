# PLEASE NOTE: If you edit this file (other than updating the version number), please
# also update scripts/nightly/get_version.py as well as that needs to generate a new
# version of this file from a template for nightly builds

from wagtail.utils.version import get_semver_version, get_version

# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
VERSION = (2, 17, 0, "alpha", 0)

__version__ = get_version(VERSION)

# Required for npm package for frontend
__semver__ = get_semver_version(VERSION)


try:
    import django

    if django.VERSION >= (3, 2):
        # The declaration is only needed for older Django versions
        pass
    else:
        default_app_config = "wagtail.apps.WagtailAppConfig"

except ImportError:
    # Django is not installed. This is most likely because pip is importing this file to get the version
    pass


def setup():
    import warnings

    from wagtail.utils.deprecation import removed_in_next_version_warning

    warnings.simplefilter("default", removed_in_next_version_warning)


setup()
