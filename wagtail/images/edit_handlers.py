from warnings import warn

from django.template.loader import render_to_string

from wagtail.admin.compare import ForeignObjectComparison
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.utils.deprecation import RemovedInWagtail219Warning


class ImageChooserPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.images.edit_handlers.ImageChooserPanel is obsolete and should be replaced by wagtail.admin.edit_handlers.FieldPanel",
            category=RemovedInWagtail219Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class ImageFieldComparison(ForeignObjectComparison):
    def htmldiff(self):
        image_a, image_b = self.get_objects()

        return render_to_string(
            "wagtailimages/widgets/compare.html",
            {
                "image_a": image_a,
                "image_b": image_b,
            },
        )
