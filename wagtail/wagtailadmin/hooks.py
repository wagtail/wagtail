# The 'hooks' module is now part of wagtailcore.
# Imports are provided here for backwards compatibility

import warnings

from wagtail.utils.deprecation import RemovedInWagtail06Warning


warnings.warn(
    "The wagtail.wagtailadmin.hooks module has been moved. "
    "Use wagtail.wagtailcore.hooks instead.", RemovedInWagtail06Warning)


from wagtail.wagtailcore.hooks import register, get_hooks
