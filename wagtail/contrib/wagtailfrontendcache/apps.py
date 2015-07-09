import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "The wagtail.contrib.wagtailfrontendcache module has been renamed to "
    "wagtail.contrib.frontendcache. Please update your INSTALLED_APPS setting.",
    RemovedInWagtail13Warning)


from wagtail.contrib.frontendcache.apps import WagtailFrontendCacheAppConfig  # noqa
