from wagtail.core import blocks


class SectionBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    body = blocks.RichTextBlock()

    class Meta:
        icon = "form"
        template = 'tests/blocks/section_block.html'
