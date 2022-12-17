from warnings import warn

from wagtail.templatetags.wagtailcore_tags import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.templatetags.wagtailcore_tags is deprecated. "
    "Use wagtail.templatetags.wagtailcore_tags instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
