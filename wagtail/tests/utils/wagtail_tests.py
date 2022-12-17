from warnings import warn

from wagtail.test.utils.wagtail_tests import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.tests.utils.wagtail_tests is deprecated. "
    "Use wagtail.test.utils.wagtail_tests instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
