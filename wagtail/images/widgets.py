import json

from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser
from wagtail.images import get_image_model
from wagtail.images.shortcuts import get_rendition_or_not_found
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter


class AdminImageChooser(BaseChooser):
    choose_one_text = _("Choose an image")
    choose_another_text = _("Change image")
    link_to_chosen_text = _("Edit this image")
    template_name = "wagtailimages/widgets/image_chooser.html"
    chooser_modal_url_name = "wagtailimages:chooser"
    icon = "image"
    classname = "image-chooser"

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
        return data

    def get_context(self, name, value_data, attrs):
        context = super().get_context(name, value_data, attrs)
        context["preview"] = value_data.get("preview", {})
        return context

    def render_js_init(self, id_, name, value_data):
        return "createImageChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailimages/js/image-chooser-modal.js"),
                versioned_static("wagtailimages/js/image-chooser.js"),
            ]
        )


class ImageChooserAdapter(WidgetAdapter):
    js_constructor = "wagtail.images.widgets.ImageChooser"

    def js_args(self, widget):
        return [
            widget.render_html("__NAME__", None, attrs={"id": "__ID__"}),
            widget.id_for_label("__ID__"),
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailimages/js/image-chooser-telepath.js"),
            ]
        )


register(ImageChooserAdapter(), AdminImageChooser)
