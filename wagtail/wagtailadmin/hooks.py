# The 'hooks' module is now part of wagtailcore.
# Imports are provided here for backwards compatibility

import warnings

warnings.warn(
    "The wagtail.wagtailadmin.hooks module has been moved. "
    "Use wagtail.wagtailcore.hooks instead.", DeprecationWarning)


from wagtail.wagtailcore.hooks import register, get_hooks
