from django.core.exceptions import ObjectDoesNotExist

from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.rich_text import EmbedHandler

# Front-end conversion


class ImageEmbedHandler(EmbedHandler):
    identifier = "image"

    @staticmethod
    def get_model():
        return get_image_model()

    @classmethod
    def expand_db_attributes(cls, attrs):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation for use on the front-end.
        """
        try:
            image = cls.get_instance(attrs)
        except ObjectDoesNotExist:
            return '<img alt="">'

        image_format = get_image_format(attrs["format"])
        return image_format.image_to_html(image, attrs.get("alt", ""))
