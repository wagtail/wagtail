from warnings import warn

from wagtail.permission_policies import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.permission_policies is deprecated. "
    "Use wagtail.permission_policies instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
