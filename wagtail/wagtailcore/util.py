import warnings

from wagtail.utils.deprecation import RemovedInWagtail06Warning


warnings.warn(
    "The wagtail.wagtailcore.util module has been renamed. "
    "Use wagtail.wagtailcore.utils instead.", RemovedInWagtail06Warning)

from .utils import *
