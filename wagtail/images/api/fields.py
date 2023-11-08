from collections import OrderedDict

from rest_framework.fields import Field

from ..models import SourceImageIOError
from ..utils import to_svg_safe_spec


class ImageRenditionField(Field):
    """
    A field that generates a rendition with the specified filter spec, and serialises
    details of that rendition.

    Example:
    "thumbnail": {
        "url": "/media/images/myimage.max-165x165.jpg",
        "full_url": "https://media.example.com/media/images/myimage.max-165x165.jpg",
        "width": 165,
        "height": 100,
        "alt": "Image alt text"
    }

    If there is an error with the source image. The dict will only contain a single
    key, "error", indicating this error:

    "thumbnail": {
        "error": "SourceImageIOError"
    }
    """

    def __init__(self, filter_spec, preserve_svg=False, *args, **kwargs):
        self.filter_spec = filter_spec
        self.preserve_svg = preserve_svg
        super().__init__(*args, **kwargs)

    def to_representation(self, image):
        try:
            if image.is_svg() and self.preserve_svg:
                filter_spec = to_svg_safe_spec(self.filter_spec)
            else:
                filter_spec = self.filter_spec

            thumbnail = image.get_rendition(filter_spec)

            return OrderedDict(
                [
                    ("url", thumbnail.url),
                    ("full_url", thumbnail.full_url),
                    ("width", thumbnail.width),
                    ("height", thumbnail.height),
                    ("alt", thumbnail.alt),
                ]
            )
        except SourceImageIOError:
            return OrderedDict(
                [
                    ("error", "SourceImageIOError"),
                ]
            )
