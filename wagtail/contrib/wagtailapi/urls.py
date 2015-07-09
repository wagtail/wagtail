import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "wagtail.contrib.wagtailapi.urls has been moved to "
    "wagtail.contrib.api.urls.",
    RemovedInWagtail13Warning)


from wagtail.contrib.api.urls import *  # noqa
