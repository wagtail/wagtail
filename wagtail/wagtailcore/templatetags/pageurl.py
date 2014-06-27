import warnings

warnings.warn(
    "The pageurl tag library has been moved to wagtailcore_tags. "
    "Use {% load wagtailcore_tags %} instead.", DeprecationWarning)


from wagtail.wagtailcore.templatetags.wagtailcore_tags import register, pageurl
