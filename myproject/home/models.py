from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import IntChoiceBlock


class TestBlock(blocks.StructBlock):
    """
    A StructBlock using IntChoiceBlock.
    """
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


class HomePage(Page):
    """
    The top-level homepage.
    """
    pass


class TestPage(Page):
    """
    Page containing a StreamField with TestBlock.
    """
    body = StreamField(
        [
            ("test", TestBlock()),
        ],
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    parent_page_types = [HomePage]

    class Meta:
        verbose_name = "Test Page"
