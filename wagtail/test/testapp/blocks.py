from wagtail import blocks


class LinkBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    url = blocks.URLBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["classname"] = (
            parent_context["classname"] if value["title"] == "Torchbox" else "normal"
        )
        return context

    def get_form_context(self, value, prefix="", errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        context["extra_var"] = "Hello from get_form_context!"
        return context

    class Meta:
        icon = "site"
        template = "tests/blocks/link_block.html"
        form_template = "tests/block_forms/link_block.html"


class SectionBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    body = blocks.RichTextBlock()

    class Meta:
        icon = "form"
        template = "tests/blocks/section_block.html"
