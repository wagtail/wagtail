from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.html_to_contentstate import AtomicBlockEntityElementHandler
from wagtail.core.rich_text.feature_registry import LinkHandler
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.images.shortcuts import get_rendition_or_not_found


# Front-end + hallo.js / editor-html conversions

class ImageHandler(LinkHandler):
    link_type = 'image'
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
    def to_open_tag(cls, attrs, for_editor):
        image = cls.get_instance(attrs)
        if image is None:
            return "<img>"

        image_format = get_image_format(attrs['format'])

        if for_editor:
            return image_format.image_to_editor_html(image, attrs.get('alt', ''))
        return image_format.image_to_html(image, attrs.get('alt', ''))


EditorHTMLImageConversionRule = [
    editor_html.EmbedTypeRule(ImageHandler.link_type, ImageHandler)
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
