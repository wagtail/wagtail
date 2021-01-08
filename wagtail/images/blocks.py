from django.template.loader import render_to_string
from django.utils.functional import cached_property

from wagtail.admin.compare import BlockComparison
from wagtail.core.blocks import ChooserBlock

from .shortcuts import get_rendition_or_not_found


class ImageChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail.images import get_image_model
        return get_image_model()

    @cached_property
    def widget(self):
        from wagtail.images.widgets import AdminImageChooser
        return AdminImageChooser()

    def get_form_state(self, value):
        value_data = self.widget.get_value_data(value)
        if value_data is None:
            return None
        else:
            return {
                'id': value_data['id'],
                'edit_link': value_data['edit_url'],
                'title': value_data['title'],
                'preview': value_data['preview'],
            }

    def render_basic(self, value, context=None):
        if value:
            return get_rendition_or_not_found(value, 'original').img_tag()
        else:
            return ''

    def get_comparison_class(self):
        return ImageChooserBlockComparison

    class Meta:
        icon = "image"


class ImageChooserBlockComparison(BlockComparison):
    def htmlvalue(self, val):
        return render_to_string("wagtailimages/widgets/compare.html", {
            'image_a': val,
            'image_b': val,
        })

    def htmldiff(self):
        return render_to_string("wagtailimages/widgets/compare.html", {
            'image_a': self.val_a,
            'image_b': self.val_b,
        })
