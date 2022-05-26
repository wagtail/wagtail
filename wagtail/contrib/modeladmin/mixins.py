from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class ThumbnailMixin:
    """
    Mixin class to help display thumbnail images in ModelAdmin listing results.
    `thumb_image_field_name` must be overridden to name a ForeignKey field on
    your model, linking to `wagtailimages.Image`.
    """

    thumb_image_field_name = "image"
    thumb_image_filter_spec = "fill-100x100"
    thumb_image_width = 50
    thumb_classname = "admin-thumb"
    thumb_col_header_text = _("image")
    thumb_default = None

    def __init__(self, *args, **kwargs):
        if "wagtail.images" not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "The `wagtail.images` app must be installed in order "
                "to use the `ThumbnailMixin` class."
            )
        self.__class__.admin_thumb.short_description = self.thumb_col_header_text
        super().__init__(*args, **kwargs)

    def admin_thumb(self, obj):
        try:
            image = getattr(obj, self.thumb_image_field_name, None)
        except AttributeError:
            raise ImproperlyConfigured(
                "The `thumb_image_field_name` attribute on your `%s` class "
                "must name a field on your model." % self.__class__.__name__
            )

        img_attrs = {
            "src": self.thumb_default,
            "width": self.thumb_image_width,
            "class": self.thumb_classname,
            "decoding": "async",
            "loading": "lazy",
        }
        if not image:
            if self.thumb_default:
                return mark_safe("<img{}>".format(flatatt(img_attrs)))
            return ""

        # try to get a rendition of the image to use
        from wagtail.images.shortcuts import get_rendition_or_not_found

        spec = self.thumb_image_filter_spec
        rendition = get_rendition_or_not_found(image, spec)
        img_attrs.update({"src": rendition.url})
        return mark_safe("<img{}>".format(flatatt(img_attrs)))
