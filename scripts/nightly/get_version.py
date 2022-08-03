"""
This script is called by the nightly build in Circle CI.

It alters the version of Wagtail to include the build date
"""

import datetime

from wagtail import VERSION

INIT_TEMPLATE = """
from wagtail.utils.version import get_semver_version, get_version

# major.minor.patch.release.number
# release must be one of alpha, beta, rc, or final
VERSION = ({major}, {minor}, {patch}, 'dev', '{datestamp}')

__version__ = get_version(VERSION)

# Required for npm package for frontend
__semver__ = get_semver_version(VERSION)
"""


print(  # noqa
    INIT_TEMPLATE.format(
        major=VERSION[0],
        minor=VERSION[1],
        patch=VERSION[2],
        datestamp=datetime.date.today().strftime("%Y%m%d"),
    )
)
