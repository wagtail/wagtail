import warnings

warnings.warn(
    "The pageurl tags has been renamed. "
    "Use wagtailcore_tags instead.", DeprecationWarning)


from wagtail.wagtailcore.templatetags.wagtailcore_tags import register
