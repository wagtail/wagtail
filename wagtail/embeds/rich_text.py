from wagtail.core.rich_text import LinkHandler
from wagtail.embeds import format
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.exceptions import EmbedException
from wagtail.embeds.models import Embed


class MediaEmbedHandler(LinkHandler):
    name = 'media'

    @staticmethod
    def get_model():
        return Embed

    @classmethod
    def get_instance(cls, attrs):
        return get_embed(attrs['url'])

    @staticmethod
    def get_id_pair_from_instance(instance):
        return 'url', instance.url

    @staticmethod
    def get_db_attributes(tag):
        return {
            'url': tag['data-url'],
        }

    @classmethod
    def expand_db_attributes(cls, attrs, for_editor):
        if for_editor:
            try:
                return format.embed_to_editor_html(attrs['url'])
            except EmbedException:
                # Could be replaced with a nice error message
                return ''
        else:
            return format.embed_to_frontend_html(attrs['url'])
