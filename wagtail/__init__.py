# PLEASE NOTE: If you edit this file, please also update scripts/nightly/get_version.py as well
# as that needs to generate a new version of this file from a template for nightly builds

from wagtail.utils.version import get_semver_version, get_version

# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
VERSION = (2, 8, 0, 'alpha', 0)

__version__ = get_version(VERSION)

# Required for npm package for frontend
__semver__ = get_semver_version(VERSION)
