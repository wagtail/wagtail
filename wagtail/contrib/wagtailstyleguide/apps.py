import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning

warnings.warn(
    "The wagtail.contrib.wagtailstyleguide module has been renamed to "
    "wagtail.contrib.styleguide. Please update your INSTALLED_APPS setting",
    RemovedInWagtail13Warning)


from wagtail.contrib.sitemaps.apps import WagtailStyleGuideAppConfig  # noqa
