from warnings import warn

from wagtail.models.audit_log import (  # noqa
    BaseLogEntry,
    BaseLogEntryManager,
    LogEntryQuerySet,
    ModelLogEntry,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.models.audit_log is deprecated. "
    "Use wagtail.models.audit_log instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
