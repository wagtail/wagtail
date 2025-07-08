import warnings

from wagtail.admin.telepath.widgets import (  # noqa: F401
    CheckboxInputAdapter,
    RadioSelectAdapter,
    SelectAdapter,
    ValidationErrorAdapter,
    WidgetAdapter,
)
from wagtail.utils.deprecation import RemovedInWagtail80Warning

warnings.warn(
    "wagtail.widget_adapters has been moved to wagtail.admin.telepath.widgets",
    RemovedInWagtail80Warning,
    stacklevel=2,
)
