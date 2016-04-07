from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib import admin

from wagtail.wagtailimages.models import Image

if hasattr(settings, 'WAGTAILIMAGES_IMAGE_MODEL') and settings.WAGTAILIMAGES_IMAGE_MODEL != 'wagtailimages.Image':
    # This installation provides its own custom image class;
    # to avoid confusion, we won't expose the unused wagtailimages.Image class
    # in the admin.
    pass
else:
    admin.site.register(Image)
