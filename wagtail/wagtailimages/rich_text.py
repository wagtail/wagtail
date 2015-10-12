from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.formats import get_image_format


class ImageEmbedHandler(object):
    """
    ImageEmbedHandler will be invoked whenever we encounter an element in HTML content
    with an attribute of data-embedtype="image". The resulting element in the database
    representation will be:
    <embed embedtype="image" id="42" format="thumb" alt="some custom alt text">
    """
    @staticmethod
    def get_db_attributes(tag):
        """
        Given a tag that we've identified as an image embed (because it has a
        data-embedtype="image" attribute), return a dict of the attributes we should
        have on the resulting <embed> element.
        """
        return {
            'id': tag['data-id'],
            'format': tag['data-format'],
            'alt': tag['data-alt'],
        }

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation.
        """
        Image = get_image_model()
        try:
            image = Image.objects.get(id=attrs['id'])
        except Image.DoesNotExist:
            return "<img>"

        image_format = get_image_format(attrs['format'])

        if for_editor:
            return image_format.image_to_editor_html(image, attrs['alt'])
        else:
            return image_format.image_to_html(image, attrs['alt'])
