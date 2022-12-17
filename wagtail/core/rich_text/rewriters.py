from warnings import warn

from wagtail.rich_text.rewriters import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.rich_text.rewriters is deprecated. "
    "Use wagtail.rich_text.rewriters instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
