from wagtail.utils.renames import rename_submodules
from wagtail.utils.deprecation import RemovedInWagtail16Warning


rename_submodules(__name__, {
    'wagtailapi': 'api',
    'wagtailfrontendcache': 'frontendcache',
    'wagtailmedusa': 'medusa',
    'wagtailroutablepage': 'routablepage',
    'wagtailsearchpromotions': 'searchpromotions',
    'wagtailstyleguide': 'styleguide',
    'wagtailsitemaps': 'sitemaps',
}, RemovedInWagtail16Warning)
