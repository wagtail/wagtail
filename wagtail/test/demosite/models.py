from datetime import date

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase

from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField
from wagtail.images.api.fields import ImageRenditionField
from wagtail.models import Orderable, Page
from wagtail.search import index

# ABSTRACT MODELS
# =============================


class AbstractLinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
    )
    link_document = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    def clean(self):
        if (
            self.link_page is None
            and self.link_document is None
            and not self.link_external
        ):
            raise ValidationError(
                "You must provide a related page, related document or an external URL"
            )

    api_fields = ("link",)

    panels = [
        FieldPanel("link_external"),
        FieldPanel("link_page"),
        FieldPanel("link_document"),
    ]

    class Meta:
        abstract = True


class AbstractRelatedLink(AbstractLinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    api_fields = ("title",) + AbstractLinkFields.api_fields

    panels = [
        FieldPanel("title"),
        MultiFieldPanel(AbstractLinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


class AbstractCarouselItem(AbstractLinkFields):
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    api_fields = (
        "image",
        "embed_url",
        "caption",
    ) + AbstractLinkFields.api_fields

    panels = [
        FieldPanel("image"),
        FieldPanel("embed_url"),
        FieldPanel("caption"),
        MultiFieldPanel(AbstractLinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


class ContactFieldsMixin(models.Model):
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=10, blank=True)

    api_fields = (
        "telephone",
        "email",
        "address_1",
        "address_2",
        "city",
        "country",
        "post_code",
    )

    panels = [
        FieldPanel("telephone"),
        FieldPanel("email"),
        FieldPanel("address_1"),
        FieldPanel("address_2"),
        FieldPanel("city"),
        FieldPanel("country"),
        FieldPanel("post_code"),
    ]

    class Meta:
        abstract = True


# PAGE MODELS
# =============================

# Home page


class HomePage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    body = RichTextField(blank=True)

    api_fields = (
        "body",
        "carousel_items",
        "related_links",
    )

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    class Meta:
        verbose_name = "homepage"


class HomePageCarouselItem(Orderable, AbstractCarouselItem):
    page = ParentalKey(
        "HomePage", related_name="carousel_items", on_delete=models.CASCADE
    )


class HomePageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "HomePage", related_name="related_links", on_delete=models.CASCADE
    )


HomePage.content_panels = Page.content_panels + [
    FieldPanel("body"),
    InlinePanel("carousel_items", label="Carousel items"),
    InlinePanel("related_links", label="Related links"),
]


# Standard pages


class StandardPage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        "intro",
        "body",
        "feed_image",
        "carousel_items",
        "related_links",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]


class StandardPageCarouselItem(Orderable, AbstractCarouselItem):
    page = ParentalKey(
        "StandardPage", related_name="carousel_items", on_delete=models.CASCADE
    )


class StandardPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "StandardPage", related_name="related_links", on_delete=models.CASCADE
    )


StandardPage.content_panels = Page.content_panels + [
    FieldPanel("intro"),
    InlinePanel("carousel_items", heading="Carousel items", label="Carousel item"),
    FieldPanel("body"),
    InlinePanel("related_links", heading="Related links", label="Related link"),
]


StandardPage.promote_panels = [
    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    FieldPanel("feed_image"),
]


class StandardIndexPage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    intro = RichTextField(blank=True)
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        "intro",
        "feed_image",
        "related_links",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
    ]


class StandardIndexPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "StandardIndexPage", related_name="related_links", on_delete=models.CASCADE
    )


StandardIndexPage.content_panels = Page.content_panels + [
    FieldPanel("intro"),
    InlinePanel("related_links", label="Related links"),
]


StandardIndexPage.promote_panels = [
    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    FieldPanel("feed_image"),
]


# Blog pages


class BlogEntryPage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    body = RichTextField()
    tags = ClusterTaggableManager(through="BlogEntryPageTag", blank=True)
    date = models.DateField("Post date")
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        APIField("body"),
        APIField("tags"),
        APIField("date"),
        APIField("feed_image"),
        APIField(
            "feed_image_thumbnail",
            serializer=ImageRenditionField("fill-300x300", source="feed_image"),
        ),
        APIField("carousel_items"),
        APIField("related_links"),
    )

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    def get_blog_index(self):
        # Find closest ancestor which is a blog index
        return BlogIndexPage.ancestor_of(self).last()


class BlogEntryPageCarouselItem(Orderable, AbstractCarouselItem):
    page = ParentalKey(
        "BlogEntryPage", related_name="carousel_items", on_delete=models.CASCADE
    )


class BlogEntryPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "BlogEntryPage", related_name="related_links", on_delete=models.CASCADE
    )


class BlogEntryPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "BlogEntryPage", related_name="tagged_items", on_delete=models.CASCADE
    )


BlogEntryPage.content_panels = Page.content_panels + [
    FieldPanel("date"),
    FieldPanel("body"),
    InlinePanel("carousel_items", label="Carousel items"),
    InlinePanel("related_links", label="Related links"),
]


BlogEntryPage.promote_panels = [
    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    FieldPanel("feed_image"),
    FieldPanel("tags"),
]


class BlogIndexPage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    intro = RichTextField(blank=True)

    api_fields = (
        "intro",
        "related_links",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
    ]

    def get_blog_entries(self):
        # Get list of live blog pages that are descendants of this page
        entries = BlogEntryPage.objects.descendant_of(self).live()

        # Order by most recent date first
        entries = entries.order_by("-date")

        return entries

    def get_context(self, request):
        # Get blog entries
        entries = self.get_blog_entries()

        # Filter by tag
        tag = request.GET.get("tag")
        if tag:
            entries = entries.filter(tags__name=tag)

        paginator = Paginator(entries, per_page=10)
        entries = paginator.get_page(request.GET.get("page"))

        # Update template context
        context = super().get_context(request)
        context["entries"] = entries
        return context


class BlogIndexPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "BlogIndexPage", related_name="related_links", on_delete=models.CASCADE
    )


BlogIndexPage.content_panels = Page.content_panels + [
    FieldPanel("intro"),
    InlinePanel("related_links", label="Related links"),
]


# Events pages


class EventPage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    AUDIENCE_CHOICES = (
        ("public", "Public"),
        ("private", "Private"),
    )

    date_from = models.DateField("Start date")
    date_to = models.DateField(
        "End date",
        null=True,
        blank=True,
        help_text="Not required if event is on a single day",
    )
    time_from = models.TimeField("Start time", null=True, blank=True)
    time_to = models.TimeField("End time", null=True, blank=True)
    audience = models.CharField(max_length=255, choices=AUDIENCE_CHOICES)
    location = models.CharField(max_length=255)
    body = RichTextField(blank=True)
    cost = models.CharField(max_length=255)
    signup_link = models.URLField(blank=True)
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        "date_from",
        "date_to",
        "time_from",
        "time_to",
        "audience",
        "location",
        "body",
        "cost",
        "signup_link",
        "feed_image",
        "carousel_items",
        "related_links",
        "speakers",
    )

    search_fields = Page.search_fields + [
        index.SearchField("get_audience_display"),
        index.SearchField("location"),
        index.SearchField("body"),
    ]

    def get_event_index(self):
        # Find closest ancestor which is an event index
        return EventIndexPage.objects.ancester_of(self).last()


class EventPageCarouselItem(Orderable, AbstractCarouselItem):
    page = ParentalKey(
        "EventPage", related_name="carousel_items", on_delete=models.CASCADE
    )


class EventPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "EventPage", related_name="related_links", on_delete=models.CASCADE
    )


class EventPageSpeaker(Orderable, AbstractLinkFields):
    page = ParentalKey("EventPage", related_name="speakers", on_delete=models.CASCADE)
    first_name = models.CharField("Name", max_length=255, blank=True)
    last_name = models.CharField("Surname", max_length=255, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        "first_name",
        "last_name",
        "image",
    )

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("image"),
        MultiFieldPanel(AbstractLinkFields.panels, "Link"),
    ]


EventPage.content_panels = Page.content_panels + [
    FieldPanel("date_from"),
    FieldPanel("date_to"),
    FieldPanel("time_from"),
    FieldPanel("time_to"),
    FieldPanel("location"),
    FieldPanel("audience"),
    FieldPanel("cost"),
    FieldPanel("signup_link"),
    InlinePanel("carousel_items", label="Carousel items"),
    FieldPanel("body"),
    InlinePanel("speakers", label="Speakers"),
    InlinePanel("related_links", label="Related links"),
]


EventPage.promote_panels = [
    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    FieldPanel("feed_image"),
]


class EventIndexPage(Page):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    intro = RichTextField(blank=True)

    api_fields = (
        "intro",
        "related_links",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
    ]

    def get_events(self):
        # Get list of live event pages that are descendants of this page
        events = EventPage.objects.descendant_of(self).live()

        # Filter events list to get ones that are either
        # running now or start in the future
        events = events.filter(date_from__gte=date.today())

        # Order by date
        events = events.order_by("date_from")

        return events


class EventIndexPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "EventIndexPage", related_name="related_links", on_delete=models.CASCADE
    )


EventIndexPage.content_panels = Page.content_panels + [
    FieldPanel("intro"),
    InlinePanel("related_links", label="Related links"),
]


# Person page


class PersonPage(Page, ContactFieldsMixin):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    intro = RichTextField(blank=True)
    biography = RichTextField(blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        "first_name",
        "last_name",
        "intro",
        "biography",
        "image",
        "feed_image",
        "related_links",
    ) + ContactFieldsMixin.api_fields

    search_fields = Page.search_fields + [
        index.SearchField("first_name"),
        index.SearchField("last_name"),
        index.SearchField("intro"),
        index.SearchField("biography"),
    ]


class PersonPageRelatedLink(Orderable, AbstractRelatedLink):
    page = ParentalKey(
        "PersonPage", related_name="related_links", on_delete=models.CASCADE
    )


PersonPage.content_panels = Page.content_panels + [
    FieldPanel("first_name"),
    FieldPanel("last_name"),
    FieldPanel("intro"),
    FieldPanel("biography"),
    FieldPanel("image"),
    MultiFieldPanel(ContactFieldsMixin.panels, "Contact"),
    InlinePanel("related_links", label="Related links"),
]


PersonPage.promote_panels = [
    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    FieldPanel("feed_image"),
]


# Contact page


class ContactPage(Page, ContactFieldsMixin):
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )
    body = RichTextField(blank=True)
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = (
        "body",
        "feed_image",
    ) + ContactFieldsMixin.api_fields

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]


ContactPage.content_panels = Page.content_panels + [
    FieldPanel("body"),
    MultiFieldPanel(ContactFieldsMixin.panels, "Contact"),
]


ContactPage.promote_panels = [
    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    FieldPanel("feed_image"),
]
