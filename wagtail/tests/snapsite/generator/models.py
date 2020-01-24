from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.core import blocks
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.images.blocks import ImageChooserBlock


class StandardPage(Page):
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title", icon='title')),
        ('paragraph', blocks.RichTextBlock(icon='pilcrow')),
        ('image', ImageChooserBlock(icon='image')),
        ('page', blocks.PageChooserBlock()),
        ('pullquote', blocks.BlockQuoteBlock(icon='openquote')),
        ('raw', blocks.RawHTMLBlock(icon='code'))
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]
