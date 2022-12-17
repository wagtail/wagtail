from warnings import warn

from wagtail.models.sites import (  # noqa
    MATCH_DEFAULT,
    MATCH_HOSTNAME,
    MATCH_HOSTNAME_DEFAULT,
    MATCH_HOSTNAME_PORT,
    get_site_for_hostname,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.sites is deprecated. "
    "Use wagtail.models.sites instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
