import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "wagtail.contrib.wagtailsitemaps.views has been moved to "
    "wagtail.contrib.sitemaps.views.",
    RemovedInWagtail13Warning)


from wagtail.contrib.sitemaps.views import *  # noqa
