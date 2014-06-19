import warnings

warnings.warn(
    "The embed_filters tags has been renamed. "
    "Use wagtailembeds_tags instead.", DeprecationWarning)


from wagtail.wagtailembeds.templatetags.wagtailembeds_tags import register
