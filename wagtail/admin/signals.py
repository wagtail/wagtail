import warnings

from wagtail.signals import init_new_page  # noqa: F401
from wagtail.utils.deprecation import RemovedInWagtail80Warning

warnings.warn(
    "wagtail.admin.signals.init_new_page has been moved to wagtail.signals.init_new_page",
    RemovedInWagtail80Warning,
    stacklevel=2,
)
