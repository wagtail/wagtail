from __future__ import absolute_import, unicode_literals

from wagtail.wagtailcore import blocks


class LinkBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    url = blocks.URLBlock()

    def get_context(self, value):
        context = super(LinkBlock, self).get_context(value)
        context['classname'] = 'important' if value['title'] == 'Torchbox' else 'normal'
        return context

    class Meta:
        icon = "site"
        template = 'tests/blocks/link_block.html'


class SectionBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    body = blocks.RichTextBlock()

    class Meta:
        icon = "form"
        template = 'tests/blocks/section_block.html'
