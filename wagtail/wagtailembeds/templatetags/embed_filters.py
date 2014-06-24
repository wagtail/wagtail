import warnings

warnings.warn(
    "The embed_filters tag library has been moved to wagtailcore_tags. "
    "Use {% load wagtailembeds_tags %} instead.", DeprecationWarning)


from wagtail.wagtailembeds.templatetags.wagtailembeds_tags import register
