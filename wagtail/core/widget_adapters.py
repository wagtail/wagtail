from warnings import warn

from wagtail.utils.deprecation import RemovedInWagtail50Warning
from wagtail.widget_adapters import *  # noqa

warn(
    "Importing from wagtail.core.widget_adapters is deprecated. "
    "Use wagtail.widget_adapters instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
