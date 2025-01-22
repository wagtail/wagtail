from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser, BaseChooserAdapter
from wagtail.images import get_image_model
from wagtail.images.shortcuts import get_rendition_or_not_found
from wagtail.telepath import register


class AdminImageChooser(BaseChooser):
    choose_one_text = _("Choose an image")
    choose_another_text = _("Change image")
    link_to_chosen_text = _("Edit this image")
    template_name = "wagtailimages/widgets/image_chooser.html"
    chooser_modal_url_name = "wagtailimages_chooser:choose"
    icon = "image"
    classname = "image-chooser"
    js_constructor = "ImageChooser"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = get_image_model()

    def get_value_data_from_instance(self, instance):
        data = super().get_value_data_from_instance(instance)
        preview_image = get_rendition_or_not_found(instance, "max-165x165")
        data["preview"] = {
            "url": preview_image.url,
            "width": preview_image.width,
            "height": preview_image.height,
        }
        data["default_alt_text"] = instance.default_alt_text
        return data

    def get_context(self, name, value_data, attrs):
        context = super().get_context(name, value_data, attrs)
        context["preview"] = value_data.get("preview", {})
        context["default_alt_text"] = value_data.get("default_alt_text", "")
        return context

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailimages/js/image-chooser-modal.js"),
                versioned_static("wagtailimages/js/image-chooser.js"),
                versioned_static("wagtailimages/js/image-chooser-telepath.js"),
            ]
        )


class ImageChooserAdapter(BaseChooserAdapter):
    js_constructor = "wagtail.images.widgets.ImageChooser"

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailimages/js/image-chooser-modal.js"),
                versioned_static("wagtailimages/js/image-chooser-telepath.js"),
            ]
        )


register(ImageChooserAdapter(), AdminImageChooser)
