from __future__ import unicode_literals

from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import python_2_unicode_compatible

from taggit.models import TaggedItemBase

from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.blocks import CharBlock, RichTextBlock
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel, TabbedInterface, ObjectList
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
from wagtail.wagtailsearch import index
from wagtail.wagtailimages.models import AbstractImage, Image
from wagtail.wagtailimages.blocks import ImageChooserBlock


EVENT_AUDIENCE_CHOICES = (
    ('public', "Public"),
    ('private', "Private"),
)


COMMON_PANELS = (
    FieldPanel('slug'),
    FieldPanel('seo_title'),
    FieldPanel('show_in_menus'),
    FieldPanel('search_description'),
)


# Link fields

class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+'
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+'
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True


# Carousel items

class CarouselItem(LinkFields):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('embed_url'),
        FieldPanel('caption'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links

class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Simple page
class SimplePage(Page):
    content = models.TextField()


class PageWithOldStyleRouteMethod(Page):
    """
    Prior to Wagtail 0.4, the route() method on Page returned an HttpResponse
    rather than a Page instance. As subclasses of Page may override route,
    we need to continue accepting this convention (albeit as a deprecated API).
    """
    content = models.TextField()
    template = 'tests/simple_page.html'

    def route(self, request, path_components):
        return self.serve(request)


# Event page

class EventPageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('tests.EventPage', related_name='carousel_items')


class EventPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('tests.EventPage', related_name='related_links')


class EventPageSpeaker(Orderable, LinkFields):
    page = ParentalKey('tests.EventPage', related_name='speakers')
    first_name = models.CharField("Name", max_length=255, blank=True)
    last_name = models.CharField("Surname", max_length=255, blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    @property
    def name_display(self):
        return self.first_name + " " + self.last_name

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        ImageChooserPanel('image'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]


class EventPage(Page):
    date_from = models.DateField("Start date", null=True)
    date_to = models.DateField(
        "End date",
        null=True,
        blank=True,
        help_text="Not required if event is on a single day"
    )
    time_from = models.TimeField("Start time", null=True, blank=True)
    time_to = models.TimeField("End time", null=True, blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
    location = models.CharField(max_length=255)
    body = RichTextField(blank=True)
    cost = models.CharField(max_length=255)
    signup_link = models.URLField(blank=True)
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = (
        index.SearchField('get_audience_display'),
        index.SearchField('location'),
        index.SearchField('body'),
    )

    password_required_template = 'tests/event_page_password_required.html'

EventPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('date_from'),
    FieldPanel('date_to'),
    FieldPanel('time_from'),
    FieldPanel('time_to'),
    FieldPanel('location'),
    FieldPanel('audience'),
    FieldPanel('cost'),
    FieldPanel('signup_link'),
    InlinePanel('carousel_items', label="Carousel items"),
    FieldPanel('body', classname="full"),
    InlinePanel('speakers', label="Speakers"),
    InlinePanel('related_links', label="Related links"),
]

EventPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
    ImageChooserPanel('feed_image'),
]


# Event index (has a separate AJAX template, and a custom template context)
class EventIndex(Page):
    intro = RichTextField(blank=True)
    ajax_template = 'tests/includes/event_listing.html'

    def get_events(self):
        return self.get_children().live().type(EventPage)

    def get_paginator(self):
        return Paginator(self.get_events(), 4)

    def get_context(self, request, page=1):
        # Pagination
        paginator = self.get_paginator()
        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            events = paginator.page(1)
        except EmptyPage:
            events = paginator.page(paginator.num_pages)

        # Update context
        context = super(EventIndex, self).get_context(request)
        context['events'] = events
        return context

    def route(self, request, path_components):
        if self.live and len(path_components) == 1:
            try:
                return self.serve(request, page=int(path_components[0]))
            except (TypeError, ValueError):
                pass

        return super(EventIndex, self).route(request, path_components)

    def get_static_site_paths(self):
        # Get page count
        page_count = self.get_paginator().num_pages

        # Yield a path for each page
        for page in range(page_count):
            yield '/%d/' % (page + 1)

        # Yield from superclass
        for path in super(EventIndex, self).get_static_site_paths():
            yield path

    def get_sitemap_urls(self):
        # Add past events url to sitemap
        return super(EventIndex, self).get_sitemap_urls() + [
            {
                'location': self.full_url + 'past/',
                'lastmod': self.latest_revision_created_at
            }
        ]

EventIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
]


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', related_name='form_fields')

class FormPage(AbstractEmailForm):
    pass

FormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel('form_fields', label="Form fields"),
    MultiFieldPanel([
        FieldPanel('to_address', classname="full"),
        FieldPanel('from_address', classname="full"),
        FieldPanel('subject', classname="full"),
    ], "Email")
]



# Snippets
class AdvertPlacement(models.Model):
    page = ParentalKey('wagtailcore.Page', related_name='advert_placements')
    advert = models.ForeignKey('tests.Advert', related_name='+')
    colour = models.CharField(max_length=255)

@python_2_unicode_compatible
class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text


register_snippet(Advert)


class StandardIndex(Page):
    """ Index for the site, not allowed to be placed anywhere """
    parent_page_types = []


# A custom panel setup where all Promote fields are placed in the Content tab instead;
# we use this to test that the 'promote' tab is left out of the output when empty
StandardIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('seo_title'),
    FieldPanel('slug'),
    InlinePanel('advert_placements', label="Adverts"),
]
StandardIndex.promote_panels = []


class StandardChild(Page):
    pass

# Test overriding edit_handler with a custom one
StandardChild.edit_handler = TabbedInterface([
    ObjectList(StandardChild.content_panels, heading='Content'),
    ObjectList(StandardChild.promote_panels, heading='Promote'),
    ObjectList(StandardChild.settings_panels, heading='Settings', classname='settings'),
    ObjectList([], heading='Dinosaurs'),
])

class BusinessIndex(Page):
    """ Can be placed anywhere, can only have Business children """
    subpage_types = ['tests.BusinessChild', 'tests.BusinessSubIndex']


class BusinessSubIndex(Page):
    """ Can be placed under BusinessIndex, and have BusinessChild children """
    subpage_types = ['tests.BusinessChild']
    parent_page_types = ['tests.BusinessIndex']


class BusinessChild(Page):
    """ Can only be placed under Business indexes, no children allowed """
    subpage_types = []
    parent_page_types = ['tests.BusinessIndex', BusinessSubIndex]


class TaggedPageTag(TaggedItemBase):
    content_object = ParentalKey('tests.TaggedPage', related_name='tagged_items')


class TaggedPage(Page):
    tags = ClusterTaggableManager(through=TaggedPageTag, blank=True)

TaggedPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('tags'),
]


class PageChooserModel(models.Model):
    page = models.ForeignKey('wagtailcore.Page', help_text='help text')

class EventPageChooserModel(models.Model):
    page = models.ForeignKey('tests.EventPage', help_text='more help text')

class SnippetChooserModel(models.Model):
    advert = models.ForeignKey(Advert, help_text='help text')

    panels = [
        SnippetChooserPanel('advert', Advert),
    ]


class CustomImageWithoutAdminFormFields(AbstractImage):
    caption = models.CharField(max_length=255)
    not_editable_field = models.CharField(max_length=255)


class CustomImageWithAdminFormFields(AbstractImage):
    caption = models.CharField(max_length=255)
    not_editable_field = models.CharField(max_length=255)

    admin_form_fields = Image.admin_form_fields + (
        'caption',
    )


class StreamModel(models.Model):
    body = StreamField([
        ('text', CharBlock()),
        ('rich_text', RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])


class StreamPage(Page):
    body = StreamField([
        ('text', CharBlock()),
        ('rich_text', RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    api_fields = ('body',)
