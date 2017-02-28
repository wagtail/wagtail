from __future__ import absolute_import, unicode_literals

import hashlib
import json
import os

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.shortcuts import render
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six import text_type
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, ObjectList, PageChooserPanel, StreamFieldPanel,
    TabbedInterface)
from wagtail.wagtailadmin.forms import WagtailAdminPageForm
from wagtail.wagtailadmin.utils import send_mail
from wagtail.wagtailcore.blocks import CharBlock, RichTextBlock
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Orderable, Page, PageManager
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField, AbstractFormSubmission
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.models import AbstractImage, AbstractRendition, Image
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
from wagtail.wagtailsnippets.models import register_snippet

from .forms import ValidatedPageForm

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
        related_name='+',
        on_delete=models.CASCADE
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE
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

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('content'),
    ]


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


# File page
class FilePage(Page):
    file_field = models.FileField()


FilePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('file_field'),
]


# Event page

class EventPageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('tests.EventPage', related_name='carousel_items', on_delete=models.CASCADE)


class EventPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('tests.EventPage', related_name='related_links', on_delete=models.CASCADE)


class EventPageSpeaker(Orderable, LinkFields):
    page = ParentalKey('tests.EventPage', related_name='speakers', on_delete=models.CASCADE)
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


@python_2_unicode_compatible
class EventCategory(models.Model):
    name = models.CharField("Name", max_length=255)

    def __str__(self):
        return self.name


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
    categories = ParentalManyToManyField(EventCategory, blank=True)

    search_fields = [
        index.SearchField('get_audience_display'),
        index.SearchField('location'),
        index.SearchField('body'),
    ]

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
    FieldPanel('categories'),
]

EventPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
    ImageChooserPanel('feed_image'),
]


# Just to be able to test multi table inheritance
class SingleEventPage(EventPage):
    excerpt = models.TextField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Short text to describe what is this action about"
    )

    # Give this page model a custom URL routing scheme
    def get_url_parts(self):
        url_parts = super(SingleEventPage, self).get_url_parts()
        if url_parts is None:
            return None
        else:
            site_id, root_url, page_path = url_parts
            return (site_id, root_url, page_path + 'pointless-suffix/')

    def route(self, request, path_components):
        if path_components == ['pointless-suffix']:
            # treat this as equivalent to a request for this page
            return super(SingleEventPage, self).route(request, [])
        else:
            # fall back to default routing rules
            return super(SingleEventPage, self).route(request, path_components)


SingleEventPage.content_panels = [FieldPanel('excerpt')] + EventPage.content_panels


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
    page = ParentalKey('FormPage', related_name='form_fields', on_delete=models.CASCADE)


class FormPage(AbstractEmailForm):
    def get_context(self, request):
        context = super(FormPage, self).get_context(request)
        context['greeting'] = "hello world"
        return context


FormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel('form_fields', label="Form fields"),
    MultiFieldPanel([
        FieldPanel('to_address', classname="full"),
        FieldPanel('from_address', classname="full"),
        FieldPanel('subject', classname="full"),
    ], "Email")
]


# FormPage with a non-HTML extension

class JadeFormField(AbstractFormField):
    page = ParentalKey('JadeFormPage', related_name='form_fields', on_delete=models.CASCADE)


class JadeFormPage(AbstractEmailForm):
    template = "tests/form_page.jade"


JadeFormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel('form_fields', label="Form fields"),
    MultiFieldPanel([
        FieldPanel('to_address', classname="full"),
        FieldPanel('from_address', classname="full"),
        FieldPanel('subject', classname="full"),
    ], "Email")
]


# FormPage with a custom FormSubmission

class FormPageWithCustomSubmission(AbstractEmailForm):
    """
    This Form page:
        * Have custom submission model
        * Have custom related_name (see `FormFieldWithCustomSubmission.page`)
        * Saves reference to a user
        * Doesn't render html form, if submission for current user is present
    """

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    def get_context(self, request, *args, **kwargs):
        context = super(FormPageWithCustomSubmission, self).get_context(request)
        context['greeting'] = "hello world"
        return context

    def get_form_fields(self):
        return self.custom_form_fields.all()

    def get_data_fields(self):
        data_fields = [
            ('username', 'Username'),
        ]
        data_fields += super(FormPageWithCustomSubmission, self).get_data_fields()

        return data_fields

    def get_submission_class(self):
        return CustomFormPageSubmission

    def process_form_submission(self, form):
        self.get_submission_class().objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            page=self, user=form.user
        )

        if self.to_address:
            addresses = [x.strip() for x in self.to_address.split(',')]
            content = '\n'.join([x[1].label + ': ' + text_type(form.data.get(x[0])) for x in form.fields.items()])
            send_mail(self.subject, content, addresses, self.from_address,)

    def serve(self, request, *args, **kwargs):
        if self.get_submission_class().objects.filter(page=self, user__pk=request.user.pk).exists():
            return render(
                request,
                self.template,
                self.get_context(request)
            )

        return super(FormPageWithCustomSubmission, self).serve(request, *args, **kwargs)


FormPageWithCustomSubmission.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('custom_form_fields', label="Form fields"),
    FieldPanel('thank_you_text', classname="full"),
    MultiFieldPanel([
        FieldPanel('to_address', classname="full"),
        FieldPanel('from_address', classname="full"),
        FieldPanel('subject', classname="full"),
    ], "Email")
]


class FormFieldWithCustomSubmission(AbstractFormField):
    page = ParentalKey(FormPageWithCustomSubmission, related_name='custom_form_fields')


class CustomFormPageSubmission(AbstractFormSubmission):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def get_data(self):
        form_data = super(CustomFormPageSubmission, self).get_data()
        form_data.update({
            'username': self.user.username,
        })

        return form_data


# Snippets
class AdvertPlacement(models.Model):
    page = ParentalKey('wagtailcore.Page', related_name='advert_placements', on_delete=models.CASCADE)
    advert = models.ForeignKey('tests.Advert', related_name='+', on_delete=models.CASCADE)
    colour = models.CharField(max_length=255)


class AdvertTag(TaggedItemBase):
    content_object = ParentalKey('Advert', related_name='tagged_items', on_delete=models.CASCADE)


@python_2_unicode_compatible
class Advert(ClusterableModel):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    tags = TaggableManager(through=AdvertTag, blank=True)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
        FieldPanel('tags'),
    ]

    def __str__(self):
        return self.text


register_snippet(Advert)


@python_2_unicode_compatible
class AdvertWithTabbedInterface(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    something_else = models.CharField(max_length=255)

    advert_panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    other_panels = [
        FieldPanel('something_else'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(advert_panels, heading='Advert'),
        ObjectList(other_panels, heading='Other'),
    ])

    def __str__(self):
        return self.text


register_snippet(AdvertWithTabbedInterface)


class StandardIndex(Page):
    """ Index for the site """
    parent_page_types = [Page]


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
], base_form_class=WagtailAdminPageForm)


class BusinessIndex(Page):
    """ Can be placed anywhere, can only have Business children """
    subpage_types = ['tests.BusinessChild', 'tests.BusinessSubIndex']


class BusinessSubIndex(Page):
    """ Can be placed under BusinessIndex, and have BusinessChild children """

    # BusinessNowherePage is 'incorrectly' added here as a possible child.
    # The rules on BusinessNowherePage prevent it from being a child here though.
    subpage_types = ['tests.BusinessChild', 'tests.BusinessNowherePage']
    parent_page_types = ['tests.BusinessIndex', 'tests.BusinessChild']


class BusinessChild(Page):
    """ Can only be placed under Business indexes, no children allowed """
    subpage_types = []
    parent_page_types = ['tests.BusinessIndex', BusinessSubIndex]


class BusinessNowherePage(Page):
    """ Not allowed to be placed anywhere """
    parent_page_types = []


class TaggedPageTag(TaggedItemBase):
    content_object = ParentalKey('tests.TaggedPage', related_name='tagged_items', on_delete=models.CASCADE)


class TaggedPage(Page):
    tags = ClusterTaggableManager(through=TaggedPageTag, blank=True)


TaggedPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('tags'),
]


class SingletonPage(Page):
    @classmethod
    def can_create_at(cls, parent):
        # You can only create one of these!
        return super(SingletonPage, cls).can_create_at(parent) \
            and not cls.objects.exists()


class PageChooserModel(models.Model):
    page = models.ForeignKey('wagtailcore.Page', help_text='help text', on_delete=models.CASCADE)


class EventPageChooserModel(models.Model):
    page = models.ForeignKey('tests.EventPage', help_text='more help text', on_delete=models.CASCADE)


class SnippetChooserModel(models.Model):
    advert = models.ForeignKey(Advert, help_text='help text', on_delete=models.CASCADE)

    panels = [
        SnippetChooserPanel('advert'),
    ]


class CustomImage(AbstractImage):
    caption = models.CharField(max_length=255)
    not_editable_field = models.CharField(max_length=255)

    admin_form_fields = Image.admin_form_fields + (
        'caption',
    )


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, related_name='renditions', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )


class StreamModel(models.Model):
    body = StreamField([
        ('text', CharBlock()),
        ('rich_text', RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])


class ExtendedImageChooserBlock(ImageChooserBlock):
    """
    Example of Block with custom get_api_representation method.
    If the request has an 'extended' query param, it returns a dict of id and title,
    otherwise, it returns the default value.
    """
    def get_api_representation(self, value, context=None):
        image_id = super(ExtendedImageChooserBlock, self).get_api_representation(value, context=context)
        if 'request' in context and context['request'].query_params.get('extended', False):
            return {
                'id': image_id,
                'title': value.title
            }
        return image_id


class StreamPage(Page):
    body = StreamField([
        ('text', CharBlock()),
        ('rich_text', RichTextBlock()),
        ('image', ExtendedImageChooserBlock()),
    ])

    api_fields = ('body',)

    content_panels = [
        FieldPanel('title'),
        StreamFieldPanel('body'),
    ]


class DefaultStreamPage(Page):
    body = StreamField([
        ('text', CharBlock()),
        ('rich_text', RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], default='')

    content_panels = [
        FieldPanel('title'),
        StreamFieldPanel('body'),
    ]


class MTIBasePage(Page):
    is_creatable = False

    class Meta:
        verbose_name = "MTI Base page"


class MTIChildPage(MTIBasePage):
    # Should be creatable by default, no need to set anything
    pass


class AbstractPage(Page):
    class Meta:
        abstract = True


@register_setting
class TestSetting(BaseSetting):
    title = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)


@register_setting(icon="tag")
class IconSetting(BaseSetting):
    pass


class NotYetRegisteredSetting(BaseSetting):
    pass


@register_setting
class FileUploadSetting(BaseSetting):
    file = models.FileField()


class BlogCategory(models.Model):
    name = models.CharField(unique=True, max_length=80)


class BlogCategoryBlogPage(models.Model):
    category = models.ForeignKey(BlogCategory, related_name="+", on_delete=models.CASCADE)
    page = ParentalKey('ManyToManyBlogPage', related_name='categories', on_delete=models.CASCADE)
    panels = [
        FieldPanel('category'),
    ]


class ManyToManyBlogPage(Page):
    """
    A page type with two different kinds of M2M relation.
    We don't formally support these, but we don't want them to cause
    hard breakages either.
    """
    body = RichTextField(blank=True)
    adverts = models.ManyToManyField(Advert, blank=True)
    blog_categories = models.ManyToManyField(
        BlogCategory, through=BlogCategoryBlogPage, blank=True)


class OneToOnePage(Page):
    """
    A Page containing a O2O relation.
    """
    body = RichTextBlock(blank=True)
    page_ptr = models.OneToOneField(Page, parent_link=True,
                                    related_name='+', on_delete=models.CASCADE)


class GenericSnippetPage(Page):
    """
    A page containing a reference to an arbitrary snippet (or any model for that matter)
    linked by a GenericForeignKey
    """
    snippet_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    snippet_object_id = models.PositiveIntegerField(null=True)
    snippet_content_object = GenericForeignKey('snippet_content_type', 'snippet_object_id')


class CustomImageFilePath(AbstractImage):
    def get_upload_to(self, filename):
        """Create a path that's file-system friendly.

        By hashing the file's contents we guarantee an equal distribution
        of files within our root directories. This also gives us a
        better chance of uploading images with the same filename, but
        different contents - this isn't guaranteed as we're only using
        the first three characters of the checksum.
        """
        original_filepath = super(CustomImageFilePath, self).get_upload_to(filename)
        folder_name, filename = original_filepath.split(os.path.sep)

        # Ensure that we consume the entire file, we can't guarantee that
        # the stream has not be partially (or entirely) consumed by
        # another process
        original_position = self.file.tell()
        self.file.seek(0)
        hash256 = hashlib.sha256()

        while True:
            data = self.file.read(256)
            if not data:
                break
            hash256.update(data)
        checksum = hash256.hexdigest()

        self.file.seek(original_position)
        return os.path.join(folder_name, checksum[:3], filename)


class CustomManager(PageManager):
    pass


class CustomManagerPage(Page):
    objects = CustomManager()


class MyBasePage(Page):
    """
    A base Page model, used to set site-wide defaults and overrides.
    """
    objects = CustomManager()

    class Meta:
        abstract = True


class MyCustomPage(MyBasePage):
    pass


class ValidatedPage(Page):
    foo = models.CharField(max_length=255)

    base_form_class = ValidatedPageForm
    content_panels = Page.content_panels + [
        FieldPanel('foo'),
    ]


class DefaultRichTextFieldPage(Page):
    body = RichTextField()

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('body'),
    ]


class DefaultRichBlockFieldPage(Page):
    body = StreamField([
        ('rich_text', RichTextBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body')
    ]


class CustomRichTextFieldPage(Page):
    body = RichTextField(editor='custom')

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('body'),
    ]


class CustomRichBlockFieldPage(Page):
    body = StreamField([
        ('rich_text', RichTextBlock(editor='custom')),
    ])

    content_panels = [
        FieldPanel('title', classname="full title"),
        StreamFieldPanel('body'),
    ]


# a page that only contains RichTextField within an InlinePanel,
# to test that the inline child's form media gets pulled through
class SectionedRichTextPageSection(Orderable):
    page = ParentalKey('tests.SectionedRichTextPage', related_name='sections', on_delete=models.CASCADE)
    body = RichTextField()

    panels = [
        FieldPanel('body')
    ]


class SectionedRichTextPage(Page):
    content_panels = [
        FieldPanel('title', classname="full title"),
        InlinePanel('sections')
    ]


class InlineStreamPageSection(Orderable):
    page = ParentalKey('tests.InlineStreamPage', related_name='sections', on_delete=models.CASCADE)
    body = StreamField([
        ('text', CharBlock()),
        ('rich_text', RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])
    panels = [
        StreamFieldPanel('body')
    ]


class InlineStreamPage(Page):
    content_panels = [
        FieldPanel('title', classname="full title"),
        InlinePanel('sections')
    ]


class UserProfile(models.Model):
    # Wagtail's schema must be able to coexist alongside a custom UserProfile model
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    favourite_colour = models.CharField(max_length=255)


class PanelSettings(TestSetting):
    panels = [
        FieldPanel('title')
    ]


class TabbedSettings(TestSetting):
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel('title')
        ], heading='First tab'),
        ObjectList([
            FieldPanel('email')
        ], heading='Second tab'),
    ])
