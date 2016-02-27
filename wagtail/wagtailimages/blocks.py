from __future__ import absolute_import, unicode_literals

from django.utils.functional import cached_property

from wagtail.wagtailcore.blocks import ChooserBlock

from .shortcuts import get_rendition_or_not_found


class ImageChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail.wagtailimages.models import get_image_model
        return get_image_model()

    @cached_property
    def widget(self):
        from wagtail.wagtailimages.widgets import AdminImageChooser
        return AdminImageChooser

    def render_basic(self, value):
        if value:
            return get_rendition_or_not_found(value, 'original').img_tag()
        else:
            return ''

    class Meta:
        icon = "image"
