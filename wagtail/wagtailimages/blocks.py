from django.utils.functional import cached_property

from wagtail.wagtailcore.blocks import ChooserBlock

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
            return value.get_rendition('original').img_tag()
        else:
            return ''
