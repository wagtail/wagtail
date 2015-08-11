import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "wagtail.contrib.wagtailmedusa.renderers has been moved to "
    "wagtail.contrib.staticsitegen.renderers.",
    RemovedInWagtail13Warning)


from wagtail.contrib.staticsitegen.renderers import *  # noqa
