from warnings import warn

from wagtail.blocks.base import *  # NOQA
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.blocks.base is deprecated. "
    "Use wagtail.blocks.base instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
