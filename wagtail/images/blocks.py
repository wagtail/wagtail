from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.functional import cached_property

from wagtail.admin.compare import BlockComparison
from wagtail.blocks import BooleanBlock, CharBlock, ChooserBlock, StructBlock
from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.images.models import AbstractImage
from wagtail.telepath import register

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

    def render_basic(self, value, context=None):
        if value:
            return get_rendition_or_not_found(value, "original").img_tag()
        else:
            return ""

    def get_comparison_class(self):
        return ImageChooserBlockComparison

    class Meta:
        icon = "image"


class ImageChooserBlockComparison(BlockComparison):
    def htmlvalue(self, val):
        return render_to_string(
            "wagtailimages/widgets/compare.html",
            {
                "image_a": val,
                "image_b": val,
            },
        )

    def htmldiff(self):
        return render_to_string(
            "wagtailimages/widgets/compare.html",
            {
                "image_a": self.val_a,
                "image_b": self.val_b,
            },
        )


class ImageBlock(StructBlock):
    image = ImageChooserBlock(required=True)
    decorative = BooleanBlock(
        default=False, required=False, label="Image is decorative"
    )
    alt_text = CharBlock(required=False)

    def get_searchable_content(self, value):
        return []

    def _struct_value_to_image(self, struct_value):
        image = struct_value.get("image")
        decorative = struct_value.get("decorative")
        if image:
            # If the image is decorative, set alt_text to an empty string
            image.contextual_alt_text = (
                "" if decorative else struct_value.get("alt_text", "")
            )
            image.decorative = decorative
        return image

    def to_python(self, value):
        struct_value = super().to_python(value)
        return self._struct_value_to_image(struct_value)

    def bulk_to_python(self, values):
        struct_values = super().bulk_to_python(values)
        return [
            self._struct_value_to_image(struct_value) for struct_value in struct_values
        ]

    def value_from_datadict(self, data, files, prefix):
        struct_value = super().value_from_datadict(data, files, prefix)
        return self._struct_value_to_image(struct_value)

    def clean(self, value):
        if value is None:
            return None

        if not isinstance(value, AbstractImage):
            raise ValidationError("Expected an image instance, got %r" % value)

        if not value.contextual_alt_text and not value.decorative:
            raise ValidationError("Alt text is required for non-decorative images")

        return value

    def normalize(self, value):
        if value is None or isinstance(value, AbstractImage):
            return value
        else:
            struct_value = super().normalize(value)
            return self._struct_value_to_image(struct_value)

    def get_form_state(self, value):
        return {
            "image": self.child_blocks["image"].get_form_state(value),
            "alt_text": value and value.contextual_alt_text,
            "decorative": value and value.decorative,
        }

    def get_prep_value(self, value):
        return {
            "image": self.child_blocks["image"].get_prep_value(value),
            "alt_text": value and value.contextual_alt_text,
            "decorative": value and value.decorative,
        }

    def extract_references(self, value):
        return self.child_blocks["image"].extract_references(value)

    class Meta:
        icon = "image"
        template = "wagtailimages/widgets/image.html"


class ImageBlockAdapter(StructBlockAdapter):
    js_constructor = "wagtail.images.blocks.ImageBlock"

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ["wagtailimages/js/image-chooser-modified.js"],
            css=structblock_media._css,
        )


register(ImageBlockAdapter(), ImageBlock)
