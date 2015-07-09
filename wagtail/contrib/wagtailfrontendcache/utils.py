import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "wagtail.contrib.wagtailfrontendcache.utils has been moved to "
    "wagtail.contrib.frontendcache.utils.",
    RemovedInWagtail13Warning)


from wagtail.contrib.frontendcache.utils import *  # noqa
