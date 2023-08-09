from warnings import warn

from wagtail.test.utils import *  # noqa: F403
from wagtail.utils.deprecation import RemovedInWagtail60Warning

warn(
    "Importing from wagtail.tests.utils is deprecated. "
    "Use wagtail.test.utils instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail60Warning,
    stacklevel=2,
)
