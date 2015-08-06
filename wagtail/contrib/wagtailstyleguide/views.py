import warnings
from wagtail.utils.deprecation import RemovedInWagtail13Warning


warnings.warn(
    "wagtail.contrib.wagtailstyleguide.views has been moved to "
    "wagtail.contrib.styleguide.views.",
    RemovedInWagtail13Warning)


from wagtail.contrib.styleguide.views import *  # noqa
