from warnings import warn

from wagtail.rich_text import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.rich_text is deprecated. "
    "Use wagtail.rich_text instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
