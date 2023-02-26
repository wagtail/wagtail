from django.conf import settings
from django.forms import widgets


class SlugInput(widgets.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {
            "data-controller": "w-slug",
            "data-action": "blur->w-slug#slugify",
            "data-w-slug-allow-unicode-value": getattr(
                settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True
            ),
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
