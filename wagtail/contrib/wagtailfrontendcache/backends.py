import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "wagtail.contrib.wagtailfrontendcache.backends has been moved to "
    "wagtail.contrib.frontendcache.backends.",
    RemovedInWagtail13Warning)


from wagtail.contrib.frontendcache.backends import *  # noqa
