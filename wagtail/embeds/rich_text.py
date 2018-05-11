from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.html_to_contentstate import AtomicBlockEntityElementHandler
from wagtail.embeds import embeds, format
from wagtail.embeds.exceptions import EmbedException


# Front-end conversion

def media_embedtype_handler(attrs):
    """
    Given a dict of attributes from the <embed> tag, return the real HTML
    representation for use on the front-end.
    """
    return format.embed_to_frontend_html(attrs['url'])


# hallo.js / editor-html conversion

class MediaEmbedHandler:
    """
    MediaEmbedHandler will be invoked whenever we encounter an element in HTML content
    with an attribute of data-embedtype="media". The resulting element in the database
    representation will be:
    <embed embedtype="media" url="http://vimeo.com/XXXXX">
    """
    @staticmethod
    def get_db_attributes(tag):
        """
        Given a tag that we've identified as a media embed (because it has a
        data-embedtype="media" attribute), return a dict of the attributes we should
        have on the resulting <embed> element.
        """
        return {
            'url': tag['data-url'],
        }

    @staticmethod
    def expand_db_attributes(attrs):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation for use within the editor.
        """
        try:
            return format.embed_to_editor_html(attrs['url'])
        except EmbedException:
            # Could be replaced with a nice error message
            return ''


EditorHTMLEmbedConversionRule = [
    editor_html.EmbedTypeRule('media', MediaEmbedHandler)
]


# draft.js / contentstate conversion

def media_embed_entity(props):
    """
    Helper to construct elements of the form
    <embed embedtype="media" url="https://www.youtube.com/watch?v=y8Kyi0WNg40"/>
    when converting from contentstate data
    """
    return DOM.create_element('embed', {
        'embedtype': 'media',
        'url': props.get('url'),
    })


class MediaEmbedElementHandler(AtomicBlockEntityElementHandler):
    """
    Rule for building an embed entity when converting from database representation
    to contentstate
    """
    def create_entity(self, name, attrs, state, contentstate):
        try:
            embed_obj = embeds.get_embed(attrs['url'])
            embed_data = {
                'embedType': embed_obj.type,
                'url': embed_obj.url,
                'providerName': embed_obj.provider_name,
                'authorName': embed_obj.author_name,
                'thumbnail': embed_obj.thumbnail_url,
                'title': embed_obj.title,
            }
        except EmbedException:
            embed_data = {'url': attrs['url']}
        return Entity('EMBED', 'IMMUTABLE', embed_data)


ContentstateMediaConversionRule = {
    'from_database_format': {
        'embed[embedtype="media"]': MediaEmbedElementHandler(),
    },
    'to_database_format': {
        'entity_decorators': {'EMBED': media_embed_entity}
    }
}
