from django.apps import AppConfig

from . import checks  # NOQA


class WagtailImagesAppConfig(AppConfig):
    name = 'wagtail.wagtailimages'
    label = 'wagtailimages'
    verbose_name = "Wagtail images"
