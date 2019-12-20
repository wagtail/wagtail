from django.template.loader import render_to_string

from wagtail.admin.compare import ForeignObjectComparison
from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminImageChooser


class ImageChooserPanel(BaseChooserPanel):
    object_type_name = "image"

    def widget_overrides(self):
        return {self.field_name: AdminImageChooser}

    def get_comparison_class(self):
        return ImageFieldComparison


class ImageFieldComparison(ForeignObjectComparison):
    def htmldiff(self):
        image_a, image_b = self.get_objects()

        return render_to_string("wagtailimages/widgets/compare.html", {
            'image_a': image_a,
            'image_b': image_b,
        })
