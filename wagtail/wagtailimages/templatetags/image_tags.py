import warnings

warnings.warn(
    "The image_tags tags has been renamed. "
    "Use wagtailimages_tags instead.", DeprecationWarning)


from wagtail.wagtailimages.templatetags.wagtailimages_tags import register
