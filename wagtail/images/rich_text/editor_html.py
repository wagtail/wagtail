from wagtail.admin.rich_text.converters import editor_html
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format


# hallo.js / editor-html conversion

class ImageEmbedHandler:
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
    def expand_db_attributes(attrs):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation for use within the editor.
        """
        Image = get_image_model()
        try:
            image = Image.objects.get(id=attrs['id'])
        except Image.DoesNotExist:
            return '<img alt="">'

        image_format = get_image_format(attrs['format'])

        return image_format.image_to_editor_html(image, attrs.get('alt', ''))


EditorHTMLImageConversionRule = [
    editor_html.EmbedTypeRule('image', ImageEmbedHandler)
]
