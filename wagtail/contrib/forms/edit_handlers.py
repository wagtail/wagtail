from warnings import warn

from wagtail.contrib.forms.panels import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.contrib.forms.edit_handlers is deprecated. "
    "Use wagtail.contrib.forms.panels instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
