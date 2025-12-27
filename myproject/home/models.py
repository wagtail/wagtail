from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import IntChoiceBlock  # local import last

# StructBlock using the custom IntChoiceBlock
class TestBlock(blocks.StructBlock):
    number = IntChoiceBlock(
        choices=[
            (1, "One"),
            (2, "Two"),
            (3, "Three"),
        ],
        default=1,
    )

    class Meta:
        icon = "placeholder"

# HomePage definition
class HomePage(Page):
    pass

# Page using the TestBlock
class TestPage(Page):
    body = StreamField([
        ('test', TestBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    parent_page_types = [HomePage]  # direct reference to HomePage

    class Meta:
        verbose_name = "Test Page"
