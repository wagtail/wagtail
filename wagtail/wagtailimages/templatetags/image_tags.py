import warnings

warnings.warn(
    "The image_tags tag library has been moved to wagtailcore_tags. "
    "Use {% load wagtailimages_tags %} instead.", DeprecationWarning)


from wagtail.wagtailimages.templatetags.wagtailimages_tags import register, image
