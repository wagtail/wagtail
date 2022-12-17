from warnings import warn

from wagtail.rich_text.feature_registry import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.rich_text.feature_registry is deprecated. "
    "Use wagtail.rich_text.feature_registry instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
