import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "The wagtail.contrib.wagtailapi module has been renamed to "
    "wagtail.contrib.api. Please update your INSTALLED_APPS setting",
    RemovedInWagtail13Warning)


from wagtail.contrib.api.apps import WagtailAPIAppConfig  # noqa
