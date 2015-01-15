from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.encoding import python_2_unicode_compatible
from django.conf.urls import url
from django.http import HttpResponse

from taggit.models import TaggedItemBase

from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailsearch import index
from wagtail.contrib.wagtailroutablepage.models import RoutablePage


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


class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True,
                                 **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=255, blank=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    USERNAME_FIELD = 'username'

    objects = CustomUserManager()

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.first_name


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
    InlinePanel(EventPage, 'carousel_items', label="Carousel items"),
    FieldPanel('body', classname="full"),
    InlinePanel(EventPage, 'speakers', label="Speakers"),
    InlinePanel(EventPage, 'related_links', label="Related links"),
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
    InlinePanel(FormPage, 'form_fields', label="Form fields"),
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


# AlphaSnippet and ZuluSnippet are for testing ordering of
# snippets when registering.  They are named as such to ensure
# thier ordering is clear.  They are registered during testing
# to ensure specific [in]correct register ordering

# AlphaSnippet is registered during TestSnippetOrdering
@python_2_unicode_compatible
class AlphaSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


# ZuluSnippet is registered during TestSnippetOrdering
@python_2_unicode_compatible
class ZuluSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class StandardIndex(Page):
    """ Index for the site, not allowed to be placed anywhere """
    parent_page_types = []


StandardIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(StandardIndex, 'advert_placements', label="Adverts"),
]


class StandardChild(Page):
    pass


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


class SearchTest(models.Model, index.Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()
    live = models.BooleanField(default=False)
    published_date = models.DateField(null=True)

    search_fields = [
        index.SearchField('title', partial_match=True),
        index.SearchField('content'),
        index.SearchField('callable_indexed_field'),
        index.FilterField('title'),
        index.FilterField('live'),
        index.FilterField('published_date'),
    ]

    def callable_indexed_field(self):
        return "Callable"

    @classmethod
    def get_indexed_objects(cls):
        indexed_objects = super(SearchTest, cls).get_indexed_objects()

        # Exclude SearchTests that have a SearchTestChild to stop update_index creating duplicates
        if cls is SearchTest:
            indexed_objects = indexed_objects.exclude(
                id__in=SearchTestChild.objects.all().values_list('searchtest_ptr_id', flat=True)
            )

        # Exclude SearchTests that have the title "Don't index me!"
        indexed_objects = indexed_objects.exclude(title="Don't index me!")

        return indexed_objects

    def get_indexed_instance(self):
        # Check if there is a SearchTestChild that descends from this
        child = SearchTestChild.objects.filter(searchtest_ptr_id=self.id).first()

        # Return the child if there is one, otherwise return self
        return child or self

class SearchTestChild(SearchTest):
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    extra_content = models.TextField()

    search_fields = SearchTest.search_fields + [
        index.SearchField('subtitle', partial_match=True),
        index.SearchField('extra_content'),
    ]


def routable_page_external_view(request, arg):
    return HttpResponse("EXTERNAL VIEW: " + arg)

class RoutablePageTest(RoutablePage):
    subpage_urls = (
        url(r'^$', 'main', name='main'),
        url(r'^archive/year/(\d+)/$', 'archive_by_year', name='archive_by_year'),
        url(r'^archive/author/(?P<author_slug>.+)/$', 'archive_by_author', name='archive_by_author'),
        url(r'^external/(.+)/$', routable_page_external_view, name='external_view')
    )

    def archive_by_year(self, request, year):
        return HttpResponse("ARCHIVE BY YEAR: " + str(year))

    def archive_by_author(self, request, author_slug):
        return HttpResponse("ARCHIVE BY AUTHOR: " + author_slug)

    def main(self, request):
        return HttpResponse("MAIN VIEW")


class TaggedPageTag(TaggedItemBase):
    content_object = ParentalKey('tests.TaggedPage', related_name='tagged_items')


class TaggedPage(Page):
    tags = ClusterTaggableManager(through=TaggedPageTag, blank=True)
