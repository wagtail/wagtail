from wagtail.core.rich_text import LinkHandler
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format


class ImageEmbedHandler(LinkHandler):
    name = 'image'
    tag_name = 'img'

    @staticmethod
    def get_model():
        return get_image_model()

    @staticmethod
    def get_db_attributes(tag):
        return {
            'id': tag['data-id'],
            'format': tag['data-format'],
            'alt': tag['data-alt'],
        }

    @classmethod
    def expand_db_attributes(cls, attrs, for_editor):
        image = cls.get_instance(attrs)
        if image is None:
            return "<img>"

        image_format = get_image_format(attrs['format'])

        if for_editor:
            return image_format.image_to_editor_html(image, attrs['alt'])
        return image_format.image_to_html(image, attrs['alt'])
