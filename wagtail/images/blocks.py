from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.compare import BlockComparison, StructBlockComparison
from wagtail.blocks import BooleanBlock, CharBlock, ChooserBlock, StructBlock
from wagtail.blocks.struct_block import StructBlockAdapter, StructBlockValidationError
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
    """
    An usage of ImageChooserBlock with support for alt text.
    For backward compatibility, this block overrides necessary methods to change
    the StructValue to be an Image model instance, making it compatible in
    places where ImageChooserBlock was used.
    """

    image = ImageChooserBlock(required=True)
    decorative = BooleanBlock(
        default=False, required=False, label=_("Image is decorative")
    )
    alt_text = CharBlock(required=False, label=_("Alt text"))

    def __init__(self, required=True, **kwargs):
        super().__init__(
            [
                ("image", ImageChooserBlock(required=required)),
                (
                    "decorative",
                    BooleanBlock(
                        default=False, required=False, label=_("Image is decorative")
                    ),
                ),
                ("alt_text", CharBlock(required=False, label=_("Alt text"))),
            ],
            **kwargs,
        )

    def deconstruct(self):
        """
        For typical StructBlock subclasses, it makes sense for the deconstructed block object to be a basic StructBlock
        with the child blocks passed to the constructor (because this is largely functionally identical to the
        subclass, and avoids embedding a reference to a potentially-volatile custom class in migrations).

        This is not the case for ImageBlock, as it overrides enough of StructBlock's behaviour that a basic StructBlock
        is not a suitable substitute - and also has an incompatible constructor signature (as we don't want to support
        passing child blocks to it).

        Therefore, we opt out of the standard StructBlock deconstruction behaviour here, and always
        deconstruct an ImageBlock as an ImageBlock.
        """
        return ("wagtail.images.blocks.ImageBlock", [], self._constructor_kwargs)

    def deconstruct_with_lookup(self, lookup):
        return self.deconstruct()

    @classmethod
    def construct_from_lookup(cls, lookup, *args, **kwargs):
        return cls(**kwargs)

    def get_searchable_content(self, value):
        if not self.search_index or not value:
            return []

        return self.child_blocks["alt_text"].get_searchable_content(
            value.contextual_alt_text
        )

    def _struct_value_to_image(self, struct_value):
        image = struct_value.get("image")
        decorative = struct_value.get("decorative")
        if image:
            # If the image is decorative, set alt_text to an empty string
            image.contextual_alt_text = (
                "" if decorative else struct_value.get("alt_text")
            )
            image.decorative = decorative
        return image

    def _image_to_struct_value(self, image):
        return {
            "image": image,
            "alt_text": image and image.contextual_alt_text,
            "decorative": image and image.decorative,
        }

    def to_python(self, value):
        # For backward compatibility with ImageChooserBlock
        if value is None or isinstance(value, int):
            image = self.child_blocks["image"].to_python(value)
            struct_value = {
                "image": image,
                "decorative": False,
                "alt_text": (image.default_alt_text if image else ""),
            }
        else:
            struct_value = super().to_python(value)
        return self._struct_value_to_image(struct_value)

    def bulk_to_python(self, values):
        values = list(values)

        if values and all(value is None or isinstance(value, int) for value in values):
            # `values` looks like a list of image IDs and/or None values (as we might encounter
            # if an ImageChooserBlock has been changed to an ImageBlock with no data migration)
            image_values = self.child_blocks["image"].bulk_to_python(values)

            struct_values = [
                {
                    "image": image,
                    "decorative": False,
                    "alt_text": (image.default_alt_text if image else ""),
                }
                for image in image_values
            ]

        else:
            # Treat `values` as the standard ImageBlock representation - a (possibly empty) list of
            # dicts containing `image`, `decorative` and `alt_text` keys to be handled by the
            # StructBlock superclass
            struct_values = super().bulk_to_python(values)

        return [
            self._struct_value_to_image(struct_value) for struct_value in struct_values
        ]

    def value_from_datadict(self, data, files, prefix):
        struct_value = super().value_from_datadict(data, files, prefix)
        return self._struct_value_to_image(struct_value)

    def clean(self, value):
        try:
            self.child_blocks["image"].clean(value)
        except ValidationError as e:
            raise StructBlockValidationError(
                block_errors={"image": e},
            )

        if value and not value.contextual_alt_text and not value.decorative:
            raise StructBlockValidationError(
                block_errors={
                    "alt_text": ValidationError(
                        _(
                            "Please add some alt text for your image or mark it as decorative"
                        )
                    )
                }
            )

        return value

    def normalize(self, value):
        if value is None or isinstance(value, AbstractImage):
            return value
        else:
            struct_value = super().normalize(value)
            return self._struct_value_to_image(struct_value)

    def get_form_context(self, value, prefix="", errors=None):
        dict_value = {
            "image": value,
            "alt_text": value and value.contextual_alt_text,
            "decorative": value and value.decorative,
        }
        context = super().get_form_context(dict_value, prefix=prefix, errors=errors)
        context["suggested_alt_text"] = value
        return context

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

    def get_comparison_class(self):
        return ImageBlockComparison

    def get_api_representation(self, value, context=None):
        return super().get_api_representation(
            self._image_to_struct_value(value), context=context
        )

    def render_basic(self, value, context=None):
        return self.child_blocks["image"].render_basic(value, context=context)

    def get_block_by_content_path(self, value, path_elements):
        if path_elements:
            return super().get_block_by_content_path(
                self._image_to_struct_value(value), path_elements
            )
        else:
            return self.bind(value)

    class Meta:
        icon = "image"
        template = "wagtailimages/widgets/image.html"


class ImageBlockAdapter(StructBlockAdapter):
    js_constructor = "wagtail.images.blocks.ImageBlock"

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ["wagtailimages/js/image-block.js"],
            css=structblock_media._css,
        )


register(ImageBlockAdapter(), ImageBlock)


class ImageBlockComparison(StructBlockComparison):
    def __init__(self, block, exists_a, exists_b, val_a, val_b):
        super().__init__(
            block,
            exists_a,
            exists_b,
            block._image_to_struct_value(val_a),
            block._image_to_struct_value(val_b),
        )

    def htmlvalue(self, val):
        if isinstance(val, AbstractImage):
            return super().htmlvalue(self.block._image_to_struct_value(val))
        else:
            return super().htmlvalue(val)
