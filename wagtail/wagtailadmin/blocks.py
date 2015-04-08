import warnings

warnings.warn("wagtail.wagtailadmin.blocks has moved to wagtail.wagtailcore.blocks", UserWarning, stacklevel=2)

from wagtail.wagtailcore.blocks import *  # noqa
