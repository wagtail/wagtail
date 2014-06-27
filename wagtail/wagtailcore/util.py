import warnings

warnings.warn(
    "The wagtail.wagtailcore.util module has been renamed. "
    "Use wagtail.wagtailcore.utils instead.", DeprecationWarning)

from .utils import *
