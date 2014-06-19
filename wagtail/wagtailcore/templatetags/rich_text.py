import warnings

warnings.warn(
    "The rich_text tags has been renamed. "
    "Use wagtailrichtext_tags instead.", DeprecationWarning)


from wagtail.wagtailcore.templatetags.wagtailrichtext_tags import register
