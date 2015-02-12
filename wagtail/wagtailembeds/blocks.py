from wagtail.wagtailadmin import blocks

from wagtail.wagtailembeds.format import embed_to_frontend_html


class EmbedBlock(blocks.URLBlock):
    def render_basic(self, value):
        return embed_to_frontend_html(value)
