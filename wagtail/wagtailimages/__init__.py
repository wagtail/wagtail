from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


default_app_config = 'wagtail.wagtailimages.apps.WagtailImagesAppConfig'


def get_image_model_string():
    """Get the dotted app.Model name for the image model"""
    return getattr(settings, 'WAGTAILIMAGES_IMAGE_MODEL', 'wagtailimages.Image')


def get_image_model():
    """Get the image model from WAGTAILIMAGES_IMAGE_MODEL."""
    from django.apps import apps
    model_string = get_image_model_string()
    try:
        return apps.get_model(model_string)
    except ValueError:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "WAGTAILIMAGES_IMAGE_MODEL refers to model '%s' that has not been installed" % model_string
        )
