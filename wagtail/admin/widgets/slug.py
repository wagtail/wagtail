from django.conf import settings
from django.forms import widgets


class SlugInput(widgets.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {
            "data-controller": "w-slug",
            "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
            "data-w-slug-allow-unicode-value": getattr(
                settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True
            ),
            "data-w-slug-compare-as-param": "urlify",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
