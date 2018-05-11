from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.html_to_contentstate import AtomicBlockEntityElementHandler
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.images.shortcuts import get_rendition_or_not_found


# Front-end conversion

def image_embedtype_handler(attrs):
    """
    Given a dict of attributes from the <embed> tag, return the real HTML
    representation for use on the front-end.
    """
    Image = get_image_model()
    try:
        image = Image.objects.get(id=attrs['id'])
    except Image.DoesNotExist:
        return "<img>"

    image_format = get_image_format(attrs['format'])
    return image_format.image_to_html(image, attrs.get('alt', ''))


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
            return "<img>"

        image_format = get_image_format(attrs['format'])

        return image_format.image_to_editor_html(image, attrs.get('alt', ''))


EditorHTMLImageConversionRule = [
    editor_html.EmbedTypeRule('image', ImageEmbedHandler)
]


# draft.js / contentstate conversion

def image_entity(props):
    """
    Helper to construct elements of the form
    <embed alt="Right-aligned image" embedtype="image" format="right" id="1"/>
    when converting from contentstate data
    """
    return DOM.create_element('embed', {
        'embedtype': 'image',
        'format': props.get('format'),
        'id': props.get('id'),
        'alt': props.get('alt'),
    })


class ImageElementHandler(AtomicBlockEntityElementHandler):
    """
    Rule for building an image entity when converting from database representation
    to contentstate
    """
    def create_entity(self, name, attrs, state, contentstate):
        Image = get_image_model()
        try:
            image = Image.objects.get(id=attrs['id'])
            image_format = get_image_format(attrs['format'])
            rendition = get_rendition_or_not_found(image, image_format.filter_spec)
            src = rendition.url
        except Image.DoesNotExist:
            src = ''

        return Entity('IMAGE', 'IMMUTABLE', {
            'id': attrs['id'],
            'src': src,
            'alt': attrs.get('alt'),
            'format': attrs['format']
        })


ContentstateImageConversionRule = {
    'from_database_format': {
        'embed[embedtype="image"]': ImageElementHandler(),
    },
    'to_database_format': {
        'entity_decorators': {'IMAGE': image_entity}
    }
}
