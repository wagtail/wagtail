from wagtail.core import blocks


class SectionBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    body = blocks.RichTextBlock()
