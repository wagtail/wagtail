from warnings import warn

from wagtail.utils.deprecation import RemovedInWagtail50Warning

from ..apps import WagtailAppConfig as WagtailCoreAppConfig  # noqa

warn(
    "Importing from wagtail.core.apps is deprecated. "
    "Use wagtail.apps instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
