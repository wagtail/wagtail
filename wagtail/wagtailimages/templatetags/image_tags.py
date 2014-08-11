import warnings

from wagtail.utils.deprecation import RemovedInWagtail06Warning


warnings.warn(
    "The image_tags tag library has been moved to wagtailimages_tags. "
    "Use {% load wagtailimages_tags %} instead.", RemovedInWagtail06Warning)


from wagtail.wagtailimages.templatetags.wagtailimages_tags import register, image
