from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel


COMMON_PANELS = (
    FieldPanel('slug'),
    FieldPanel('seo_title'),
    FieldPanel('show_in_menus'),
    FieldPanel('search_description'),
)


class ChildObject(Orderable):
    page = ParentalKey('tests.TestPage', related_name='child_objects')
    chosen_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+'
    )
    chosen_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+'
    )
    chosen_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        related_name='+'
    )

    panels = [
        PageChooserPanel('chosen_page'),
        DocumentChooserPanel('chosen_document'),
        ImageChooserPanel('chosen_image'),
    ]

class TestPage(Page):
    value = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    index_me = models.BooleanField(default=True)

    def object_indexed(self):
        return self.index_me

    def calculated_indexed_field(self):
        return self.value

    indexed_fields = ('body', )

TestPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldPanel('value'),
    FieldPanel('date'),
    FieldPanel('time'),
    FieldPanel('index_me'),
    InlinePanel(TestPage, 'child_objects', label="Child objects"),
]

TestPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('slug'),
        FieldPanel('seo_title'),
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], "Common page configuration"),
]


class DerivedPage(TestPage):
    extra_field = models.CharField(max_length=255, blank=True)

    indexed_fields = ('extra_field', )


class NotIndexedPage(Page):
    indexed = False
