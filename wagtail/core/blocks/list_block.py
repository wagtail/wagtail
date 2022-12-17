from warnings import warn

from wagtail.blocks.list_block import *  # NOQA
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.blocks.list_block is deprecated. "
    "Use wagtail.blocks.list_block instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
