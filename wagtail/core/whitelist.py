from warnings import warn

from wagtail.utils.deprecation import RemovedInWagtail50Warning
from wagtail.whitelist import *  # noqa

warn(
    "Importing from wagtail.core.whitelist is deprecated. "
    "Use wagtail.whitelist instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
