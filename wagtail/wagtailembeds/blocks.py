from django import forms

from wagtail.wagtailadmin import blocks

from wagtail.wagtailembeds.format import embed_to_frontend_html


class EmbedBlock(blocks.FieldBlock):
    def __init__(self, **kwargs):
        super(EmbedBlock, self).__init__(forms.URLField(), **kwargs)

    def render_basic(self, value):
        return embed_to_frontend_html(value)
