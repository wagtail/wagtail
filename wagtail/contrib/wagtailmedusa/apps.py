import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "The wagtail.contrib.wagtailmedusa module has been renamed to "
    "wagtail.contrib.staticsitegen. Please update your INSTALLED_APPS setting",
    RemovedInWagtail13Warning)


from wagtail.contrib.staticsitegen.apps import WagtailStaticSiteGenAppConfig as WagtailMedusaAppConfig  # noqa
