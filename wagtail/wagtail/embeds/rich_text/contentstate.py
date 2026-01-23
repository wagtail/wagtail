"""
Draftail / contentstate conversion
"""

from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    AtomicBlockEntityElementHandler,
)
from wagtail.embeds import embeds
from wagtail.embeds.exceptions import EmbedException


def media_embed_entity(props):
    """
    Helper to construct elements of the form
    <embed embedtype="media" url="https://www.youtube.com/watch?v=y8Kyi0WNg40"/>
    when converting from contentstate data
    """
    return DOM.create_element(
        "embed",
        {
            "embedtype": "media",
            "url": props.get("url"),
        },
    )


class MediaEmbedElementHandler(AtomicBlockEntityElementHandler):
    """
    Rule for building an embed entity when converting from database representation
    to contentstate
    """

    def create_entity(self, name, attrs, state, contentstate):
        try:
            embed_obj = embeds.get_embed(attrs["url"])
            embed_data = {
                "embedType": embed_obj.type,
                "url": embed_obj.url,
                "providerName": embed_obj.provider_name,
                "authorName": embed_obj.author_name,
                "thumbnail": embed_obj.thumbnail_url,
                "title": embed_obj.title,
            }
        except EmbedException:
            embed_data = {"url": attrs["url"]}
        return Entity("EMBED", "IMMUTABLE", embed_data)


ContentstateMediaConversionRule = {
    "from_database_format": {
        'embed[embedtype="media"]': MediaEmbedElementHandler(),
    },
    "to_database_format": {"entity_decorators": {"EMBED": media_embed_entity}},
}
