from draftjs_exporter.constants import ENTITY_TYPES
from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.html_to_contentstate import AtomicBlockEntityElementHandler
from wagtail.admin.rich_text.editors.draftail.features import EntityFeature
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format, get_image_formats


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

def ImageEntity(props):
    """
    Helper to construct elements of the form
    <embed alt="Right-aligned image" embedtype="image" format="right" id="1"/>
    when converting from contentstate data
    """
    return DOM.create_element('embed', {
        'embedtype': 'image',
        'format': props.get('alignment'),
        'id': props.get('id'),
        'alt': props.get('altText'),
    })


class ImageFeature(EntityFeature):
    """
    Special case of EntityFeature so that we can easily define features that
    replicate the default 'image' feature with a custom list of image formats
    """
    def __init__(self, image_formats=None):
        if image_formats is None:
            format_defs = get_image_formats()
        else:
            format_defs = [get_image_format(f) for f in image_formats]

        super().__init__({
            'label': 'Image',
            'type': ENTITY_TYPES.IMAGE,
            'icon': 'icon-image',
            'imageFormats': [{'label': str(f.label), 'value': f.name} for f in format_defs],
            'source': 'ImageSource',
            'decorator': 'Image',
        })


class ImageElementHandler(AtomicBlockEntityElementHandler):
    """
    Rule for building an image entity when converting from database representation
    to contentstate
    """
    def create_entity(self, name, attrs, state, contentstate):
        return Entity('IMAGE', 'IMMUTABLE', {'altText': attrs.get('alt'), 'id': attrs['id'], 'alignment': attrs['format']})


ContentstateImageConversionRule = {
    'from_database_format': {
        'embed[embedtype="image"]': ImageElementHandler(),
    },
    'to_database_format': {
        'entity_decorators': {ENTITY_TYPES.IMAGE: ImageEntity}
    }
}
