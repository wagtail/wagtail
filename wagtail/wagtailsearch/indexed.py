import warnings

from wagtail.utils.deprecation import RemovedInWagtail08Warning


warnings.warn(
            "The wagtail.wagtailsearch.indexed module has been renamed. "
                "Use wagtail.wagtailsearch.index instead.", RemovedInWagtail08Warning)


from .index import *
