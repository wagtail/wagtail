from warnings import warn

from wagtail.test.dummy_external_storage import *  # noqa
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.tests.dummy_external_storage is deprecated. "
    "Use wagtail.test.dummy_external_storage instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
