from warnings import warn

from wagtail.admin.panels import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.admin.edit_handlers is deprecated. "
    "Use wagtail.admin.panels instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
