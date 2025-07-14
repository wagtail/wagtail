import warnings

from wagtail.admin.telepath import (  # noqa: F401
    Adapter,
    AdapterRegistry,
    JSContext,
    JSContextBase,
    WagtailAdapterRegistry,
    WagtailJSContextBase,
    adapter,
    register,
    registry,
)
from wagtail.utils.deprecation import RemovedInWagtail80Warning

warnings.warn(
    "wagtail.telepath has been moved to wagtail.admin.telepath",
    RemovedInWagtail80Warning,
    stacklevel=2,
)
