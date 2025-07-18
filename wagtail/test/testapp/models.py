import datetime
import hashlib
import os
import random
import string
import uuid

from django import forms
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from taggit.managers import TaggableManager
from taggit.models import ItemBase, TagBase, TaggedItemBase

from wagtail.admin import widgets
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.mail import send_mail
from wagtail.admin.panels import (
    FieldPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    MultipleChooserPanel,
    ObjectList,
    PublishingPanel,
    TabbedInterface,
    TitleFieldPanel,
)
from wagtail.blocks import (
    CharBlock,
    FieldBlock,
    ListBlock,
    RawHTMLBlock,
    RichTextBlock,
    StreamBlock,
    StructBlock,
)
from wagtail.compat import HTTPMethod
from wagtail.contrib.forms.forms import FormBuilder, WagtailAdminFormPageForm
from wagtail.contrib.forms.models import (
    FORM_FIELD_CHOICES,
    AbstractEmailForm,
    AbstractFormField,
    AbstractFormSubmission,
)
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.forms.views import SubmissionsListView
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.contrib.sitemaps import Sitemap
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.documents import get_document_model
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.documents.models import AbstractDocument, Document
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageBlock, ImageChooserBlock
from wagtail.images.models import AbstractImage, AbstractRendition, Image
from wagtail.models import (
    DraftStateMixin,
    LockableMixin,
    Orderable,
    Page,
    PageManager,
    PagePermissionTester,
    PageQuerySet,
    PreviewableMixin,
    RevisionMixin,
    Task,
    TaskState,
    TranslatableMixin,
    WorkflowMixin,
)
from wagtail.search import index
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet

from .forms import FormClassAdditionalFieldPageForm, ValidatedPageForm

EVENT_AUDIENCE_CHOICES = (
    ("public", _("Public")),
    ("private", _("Private")),
)


COMMON_PANELS = ("slug", "seo_title", "show_in_menus", "search_description")

CUSTOM_PREVIEW_SIZES = [
    {
        "name": "custom-mobile",
        "icon": "mobile-alt",
        "device_width": 412,
        "label": "Custom mobile preview",
    },
    {
        "name": "desktop",
        "icon": "desktop",
        "device_width": 1280,
        "label": "Original desktop",
    },
]


# Link fields


class LinkFields(models.Model):
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

    panels = [
        FieldPanel("link_external"),
        FieldPanel("link_page"),
        FieldPanel("link_document"),
    ]

    class Meta:
        abstract = True


# Carousel items


class CarouselItem(LinkFields):
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        "image",
        "embed_url",
        "caption",
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links


class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        "title",
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Simple page
class SimplePage(Page):
    content = models.TextField()
    page_description = "A simple page description"

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("content"),
    ]

    def get_admin_display_title(self):
        return "%s (simple page)" % super().get_admin_display_title()


class MultiPreviewModesPage(Page):
    preview_templates = {
        "original": "tests/simple_page.html",
        "alt#1": "tests/simple_page_alt.html",
    }
    template = preview_templates["original"]

    @property
    def preview_modes(self):
        return [("original", "Original"), ("alt#1", "Alternate")]

    @property
    def default_preview_mode(self):
        return "alt#1"

    def get_preview_template(self, request, mode_name):
        if mode_name in self.preview_templates:
            return self.preview_templates[mode_name]
        return super().get_preview_template(request, mode_name)


class CustomPreviewSizesPage(Page):
    template = "tests/simple_page.html"

    @property
    def preview_sizes(self):
        return CUSTOM_PREVIEW_SIZES

    @property
    def default_preview_size(self):
        return "desktop"


class ExcludedCopyPageNote(Orderable):
    page = ParentalKey(
        "tests.PageWithExcludedCopyField",
        related_name="special_notes",
        on_delete=models.CASCADE,
    )
    note = models.CharField(max_length=255)

    panels = [FieldPanel("note")]


# Page with Excluded Fields when copied
class PageWithExcludedCopyField(Page):
    content = models.TextField()

    # Exclude these fields and the special_notes relation from being copied
    special_field = models.CharField(blank=True, max_length=255, default="Very Special")
    special_stream = StreamField(
        [("item", CharBlock())], default=[("item", "default item")]
    )
    exclude_fields_in_copy = ["special_field", "special_notes", "special_stream"]

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("special_field"),
        FieldPanel("content"),
        FieldPanel("special_stream"),
        InlinePanel("special_notes", label="special note"),
    ]


class RelatedGenericRelation(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")


class PageWithGenericRelation(Page):
    generic_relation = GenericRelation("tests.RelatedGenericRelation")


class PageWithOldStyleRouteMethod(Page):
    """
    Prior to Wagtail 0.4, the route() method on Page returned an HttpResponse
    rather than a Page instance. As subclasses of Page may override route,
    we need to continue accepting this convention (albeit as a deprecated API).
    """

    content = models.TextField()
    template = "tests/simple_page.html"

    def route(self, request, path_components):
        return self.serve(request)


# File page
class FilePage(Page):
    file_field = models.FileField()

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        HelpPanel("remember to check for viruses"),
        FieldPanel("file_field"),
    ]


# Event page


class EventPageCarouselItem(TranslatableMixin, Orderable, CarouselItem):
    page = ParentalKey(
        "tests.EventPage", related_name="carousel_items", on_delete=models.CASCADE
    )

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        pass


class EventPageRelatedLink(TranslatableMixin, Orderable, RelatedLink):
    page = ParentalKey(
        "tests.EventPage", related_name="related_links", on_delete=models.CASCADE
    )

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        pass


class EventPageSpeakerAward(TranslatableMixin, Orderable, models.Model):
    speaker = ParentalKey(
        "tests.EventPageSpeaker", related_name="awards", on_delete=models.CASCADE
    )
    name = models.CharField("Award name", max_length=255)
    date_awarded = models.DateField(null=True, blank=True)

    panels = ["name", "date_awarded"]

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        pass


class EventPageSpeaker(TranslatableMixin, Orderable, LinkFields, ClusterableModel):
    page = ParentalKey(
        "tests.EventPage",
        related_name="speakers",
        related_query_name="speaker",
        on_delete=models.CASCADE,
    )
    first_name = models.CharField("Name", max_length=255, blank=True)
    last_name = models.CharField("Surname", max_length=255, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    @property
    def name_display(self):
        return self.first_name + " " + self.last_name

    panels = [
        "first_name",
        "last_name",
        "image",
        MultiFieldPanel(LinkFields.panels, "Link"),
        InlinePanel("awards", label="award"),
    ]

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        pass


class EventCategory(TranslatableMixin, models.Model):
    name = models.CharField("Name", max_length=255)

    def __str__(self):
        return self.name


# Override the standard WagtailAdminPageForm to add validation on start/end dates
# that appears as a non-field error


class EventPageForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()

        # Make sure that the event starts before it ends
        start_date = cleaned_data.get("date_from")
        end_date = cleaned_data.get("date_to")
        if start_date and end_date and start_date > end_date:
            raise ValidationError("The end date must be after the start date")

        return cleaned_data


class EventPage(Page):
    date_from = models.DateField("Start date", null=True)
    date_to = models.DateField(
        "End date",
        null=True,
        blank=True,
        help_text="Not required if event is on a single day",
    )
    time_from = models.TimeField("Start time", null=True, blank=True)
    time_to = models.TimeField("End time", null=True, blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
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
    categories = ParentalManyToManyField(EventCategory, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("get_audience_display"),
        index.SearchField("location"),
        index.SearchField("body"),
        index.FilterField("url_path"),
    ]

    password_required_template = "tests/event_page_password_required.html"
    base_form_class = EventPageForm

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        "date_from",
        "date_to",
        "time_from",
        "time_to",
        "location",
        FieldPanel("audience", help_text="Who this event is for"),
        "cost",
        "signup_link",
        InlinePanel("carousel_items", label="carousel item"),
        "body",
        InlinePanel(
            "speakers",
            label="speaker",
            heading="Speaker lineup",
            help_text="Put the keynote speaker first",
        ),
        InlinePanel("related_links", label="related link"),
        "categories",
        # InlinePanel related model uses `pk` not `id`
        InlinePanel("head_counts", label="head count"),
    ]

    promote_panels = [
        MultiFieldPanel(
            COMMON_PANELS, "Common page configuration", help_text="For SEO nerds only"
        ),
        FieldPanel("feed_image"),
    ]

    class Meta:
        permissions = [
            ("custom_see_panel_setting", "Can see the panel."),
            ("other_custom_see_panel_setting", "Can see the panel."),
        ]


class HeadCountRelatedModelUsingPK(models.Model):
    """Related model that uses a custom primary key (pk) not id"""

    custom_id = models.AutoField(primary_key=True)
    event_page = ParentalKey(
        EventPage, on_delete=models.CASCADE, related_name="head_counts"
    )
    related_page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="head_count_relations",
        null=True,
    )
    head_count = models.IntegerField()
    panels = [FieldPanel("head_count")]


# Override the standard WagtailAdminPageForm to add field that is not in model
# so that we can test additional potential issues like comparing versions
class FormClassAdditionalFieldPage(Page):
    location = models.CharField(max_length=255)
    body = RichTextField(blank=True)

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("location"),
        FieldPanel("body"),
        FieldPanel("code"),  # not in model, see set base_form_class
    ]

    base_form_class = FormClassAdditionalFieldPageForm


# Just to be able to test multi table inheritance
class SingleEventPage(EventPage):
    excerpt = models.TextField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Short text to describe what is this action about",
    )

    # Give this page model a custom URL routing scheme
    def get_url_parts(self, request=None):
        url_parts = super().get_url_parts(request=request)
        if url_parts is None:
            return None
        else:
            site_id, root_url, page_path = url_parts
            return (site_id, root_url, page_path + "pointless-suffix/")

    def route(self, request, path_components):
        if path_components == ["pointless-suffix"]:
            # treat this as equivalent to a request for this page
            return super().route(request, [])
        else:
            # fall back to default routing rules
            return super().route(request, path_components)

    def get_admin_display_title(self):
        return "%s (single event)" % super().get_admin_display_title()

    content_panels = [FieldPanel("excerpt")] + EventPage.content_panels


# "custom" sitemap object
class EventSitemap(Sitemap):
    pass


# Event index (has a separate AJAX template, and a custom template context)
class EventIndex(Page):
    intro = RichTextField(blank=True, max_length=50)
    ajax_template = "tests/includes/event_listing.html"

    # NOTE: Using a mix of enum and string values to test handling of both
    allowed_http_methods = [HTTPMethod.GET, "OPTIONS"]

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
        context = super().get_context(request)
        context["events"] = events
        return context

    def route(self, request, path_components):
        if self.live and len(path_components) == 1:
            try:
                return self.serve(request, page=int(path_components[0]))
            except (TypeError, ValueError):
                pass

        return super().route(request, path_components)

    def get_sitemap_urls(self, request=None):
        # Add past events url to sitemap
        return super().get_sitemap_urls(request=request) + [
            {
                "location": self.full_url + "past/",
                "lastmod": self.latest_revision_created_at,
            }
        ]

    def get_cached_paths(self):
        return super().get_cached_paths() + ["/past/"]

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("intro"),
    ]


class FormField(AbstractFormField):
    page = ParentalKey("FormPage", related_name="form_fields", on_delete=models.CASCADE)


class FormPage(AbstractEmailForm):
    def get_context(self, request):
        context = super().get_context(request)
        context["greeting"] = "hello world"
        return context

    # This is redundant (SubmissionsListView is the default view class), but importing
    # SubmissionsListView in this models.py helps us to confirm that this recipe
    # https://docs.wagtail.org/en/stable/reference/contrib/forms/customization.html#customise-form-submissions-listing-in-wagtail-admin
    # works without triggering circular dependency issues -
    # see https://github.com/wagtail/wagtail/issues/6265
    submissions_list_view_class = SubmissionsListView

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        InlinePanel("form_fields", label="form field"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
        FormSubmissionsPanel(),
    ]


# CopyForm allowing auto-increment of slugs


class CustomCopyForm(CopyForm):
    def __init__(self, *args, **kwargs):
        # call super
        super().__init__(*args, **kwargs)
        # set initial_slug as incremented slug
        suffix = 2
        parent_page = self.page.get_parent()
        if self.page.slug:
            try:
                suffix = int(self.page.slug[-1]) + 1
                base_slug = self.page.slug[:-2]

            except ValueError:
                base_slug = self.page.slug

        candidate_slug = base_slug + f"-{suffix}"
        while not Page._slug_is_available(candidate_slug, parent_page):
            suffix += 1
            candidate_slug = f"{base_slug}-{suffix}"
            candidate_slug
        allow_unicode = getattr(settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True)
        self.fields["new_slug"] = forms.SlugField(
            initial=candidate_slug,
            label=_("New slug"),
            allow_unicode=allow_unicode,
            widget=widgets.slug.SlugInput,
        )


# FormPage with a non-HTML extension


class JadeFormField(AbstractFormField):
    page = ParentalKey(
        "JadeFormPage", related_name="form_fields", on_delete=models.CASCADE
    )


class JadeFormPage(AbstractEmailForm):
    template = "tests/form_page.jade"

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        InlinePanel("form_fields", label="form field"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]


# Form page that redirects to a different page


class RedirectFormField(AbstractFormField):
    page = ParentalKey(
        "FormPageWithRedirect", related_name="form_fields", on_delete=models.CASCADE
    )


class FormPageWithRedirect(AbstractEmailForm):
    thank_you_redirect_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def get_context(self, request):
        context = super().get_context(request)
        context["greeting"] = "hello world"
        return context

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        """
        Renders the landing page OR if a receipt_page_redirect is chosen redirects to this page.
        """
        if self.thank_you_redirect_page:
            return redirect(self.thank_you_redirect_page.url, permanent=False)

        return super().render_landing_page(request, form_submission, *args, **kwargs)

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("thank_you_redirect_page"),
        InlinePanel("form_fields", label="form field"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]


# FormPage with a custom FormSubmission


class FormPageWithCustomSubmissionForm(WagtailAdminFormPageForm):
    """
    Used to validate that admin forms can validate the page's submissions via
    extending the form class.
    """

    def clean(self):
        cleaned_data = super().clean()
        from_address = cleaned_data.get("from_address")
        if from_address and "example.com" in from_address:
            raise ValidationError("Email cannot be from example.com")

        return cleaned_data


class FormPageWithCustomSubmission(AbstractEmailForm):
    """
    A ``FormPage`` with a custom FormSubmission and other extensive customizations:

    * A custom submission model
    * A custom related_name (see `FormFieldWithCustomSubmission.page`)
    * Saves reference to a user
    * Doesn't render html form, if submission for current user is present
    * A custom clean method that does not allow the ``from_address`` to be set to anything including example.com
    """

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    base_form_class = FormPageWithCustomSubmissionForm

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        context["greeting"] = "hello world"
        return context

    def get_form_fields(self):
        return self.custom_form_fields.all()

    def get_data_fields(self):
        data_fields = [
            ("useremail", "User email"),
        ]
        data_fields += super().get_data_fields()

        return data_fields

    def get_submission_class(self):
        return CustomFormPageSubmission

    def process_form_submission(self, form):
        form_submission = self.get_submission_class().objects.create(
            form_data=form.cleaned_data,
            page=self,
            user=form.user,
        )

        if self.to_address:
            addresses = [x.strip() for x in self.to_address.split(",")]
            content = "\n".join(
                [
                    x[1].label + ": " + str(form.data.get(x[0]))
                    for x in form.fields.items()
                ]
            )
            send_mail(
                self.subject,
                content,
                addresses,
                self.from_address,
            )

        # process_form_submission should now return the created form_submission
        return form_submission

    def serve(self, request, *args, **kwargs):
        if (
            self.get_submission_class()
            .objects.filter(page=self, user__pk=request.user.pk)
            .exists()
        ):
            return TemplateResponse(request, self.template, self.get_context(request))

        return super().serve(request, *args, **kwargs)

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("intro"),
        InlinePanel("custom_form_fields", label="form field"),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]


class FormFieldWithCustomSubmission(AbstractFormField):
    page = ParentalKey(
        FormPageWithCustomSubmission,
        on_delete=models.CASCADE,
        related_name="custom_form_fields",
    )


class CustomFormPageSubmission(AbstractFormSubmission):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def get_data(self):
        form_data = super().get_data()
        form_data.update(
            {
                "useremail": self.user.email,
            }
        )

        return form_data


# Custom form page with custom submission listing view and form submission


class FormFieldForCustomListViewPage(AbstractFormField):
    page = ParentalKey(
        "FormPageWithCustomSubmissionListView",
        related_name="form_fields",
        on_delete=models.CASCADE,
    )


class FormPageWithCustomSubmissionListView(AbstractEmailForm):
    """Form Page with customised submissions listing view"""

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    def get_submissions_list_view_class(self):
        from .views import CustomSubmissionsListView

        return CustomSubmissionsListView

    def get_submission_class(self):
        return CustomFormPageSubmission

    def get_data_fields(self):
        data_fields = [
            ("useremail", "User email"),
        ]
        data_fields += super().get_data_fields()

        return data_fields

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("intro"),
        InlinePanel("form_fields", label="form field"),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]


# FormPage with custom FormBuilder

EXTENDED_CHOICES = FORM_FIELD_CHOICES + (("ipaddress", "IP Address"),)


class ExtendedFormField(AbstractFormField):
    """
    Override the field_type field with extended choices
    and a custom clean_name override.
    """

    page = ParentalKey(
        "FormPageWithCustomFormBuilder",
        related_name="form_fields",
        on_delete=models.CASCADE,
    )
    field_type = models.CharField(
        verbose_name="field type", max_length=16, choices=EXTENDED_CHOICES
    )

    def get_field_clean_name(self):
        clean_name = super().get_field_clean_name()

        # scoping to field type to easily test behaviour in isolation
        if self.field_type == "number":
            return f"number_field--{clean_name}"

        # scoping to field label to easily test duplicate behaviour in isolation
        if "duplicate" in self.label:
            return "test duplicate"

        return clean_name


class CustomFormBuilder(FormBuilder):
    """
    A custom FormBuilder that has an 'ipaddress' field with
    customised create_singleline_field with shorter max_length
    """

    def create_singleline_field(self, field, options):
        options["max_length"] = 120  # usual default is 255
        return forms.CharField(**options)

    def create_ipaddress_field(self, field, options):
        return forms.GenericIPAddressField(**options)


class FormBuilderWithCustomWidget(FormBuilder):
    """
    A form builder that customizes all default field type and
    passes a `widget` parameter in the options to the parent class.
    """

    def create_singleline_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_singleline_field(field, options)

    def create_multiline_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_multiline_field(field, options)

    def create_email_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_email_field(field, options)

    def create_number_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_number_field(field, options)

    def create_url_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_url_field(field, options)

    def create_checkbox_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_checkbox_field(field, options)

    def create_checkboxes_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_checkboxes_field(field, options)

    def create_dropdown_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_dropdown_field(field, options)

    def create_multiselect_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_multiselect_field(field, options)

    def create_radio_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_radio_field(field, options)

    def create_date_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_date_field(field, options)

    def create_datetime_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_datetime_field(field, options)

    def create_hidden_field(self, field, options):
        options["widget"] = forms.TextInput(attrs={"class": "custom"})
        return super().create_hidden_field(field, options)


class FormPageWithCustomFormBuilder(AbstractEmailForm):
    """
    A Form page that has a custom form builder and uses a custom
    form field model with additional field_type choices.
    """

    form_builder = CustomFormBuilder

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        InlinePanel("form_fields", label="form field"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]


# Snippets
class AdvertPlacement(models.Model):
    page = ParentalKey(
        "wagtailcore.Page", related_name="advert_placements", on_delete=models.CASCADE
    )
    advert = models.ForeignKey(
        "tests.Advert", related_name="+", on_delete=models.CASCADE
    )
    colour = models.CharField(max_length=255)


class AdvertTag(TaggedItemBase):
    content_object = ParentalKey(
        "Advert", related_name="tagged_items", on_delete=models.CASCADE
    )


class Advert(ClusterableModel):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    tags = TaggableManager(through=AdvertTag, blank=True)

    panels = [
        FieldPanel("url"),
        FieldPanel("text"),
        FieldPanel("tags"),
    ]

    def __str__(self):
        return self.text


register_snippet(Advert)


class AdvertWithCustomPrimaryKey(ClusterableModel):
    advert_id = models.CharField(max_length=255, primary_key=True)
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel("url"),
        FieldPanel("text"),
    ]

    def __str__(self):
        return self.text


register_snippet(AdvertWithCustomPrimaryKey)


class AdvertWithCustomUUIDPrimaryKey(index.Indexed, ClusterableModel):
    advert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL)

    panels = [
        FieldPanel("url"),
        FieldPanel("text"),
        FieldPanel("page"),
    ]

    search_fields = [
        index.SearchField("text"),
    ]

    def __str__(self):
        return self.text


register_snippet(AdvertWithCustomUUIDPrimaryKey)


class AdvertWithTabbedInterface(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    something_else = models.CharField(max_length=255)

    advert_panels = [
        FieldPanel("url"),
        FieldPanel("text"),
    ]

    other_panels = [
        FieldPanel("something_else"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(advert_panels, heading="Advert"),
            ObjectList(
                other_panels, heading="Other", help_text="Other panels help text"
            ),
        ],
        help_text="Top-level help text",
    )

    def __str__(self):
        return self.text

    class Meta:
        ordering = ("text",)


register_snippet(AdvertWithTabbedInterface)


class CustomManager(models.Manager):
    pass


class ModelWithCustomManager(models.Model):
    instances = CustomManager()


register_snippet(ModelWithCustomManager)


# Models with RevisionMixin
class RevisableModel(RevisionMixin, models.Model):
    text = models.TextField()


class RevisableChildModel(RevisableModel):
    secret_text = models.TextField(blank=True, default="")

    # The edit_handler is defined on the viewset


class RevisableGrandChildModel(RevisableChildModel):
    pass


# Models with DraftStateMixin
class DraftStateModel(DraftStateMixin, LockableMixin, RevisionMixin, models.Model):
    text = models.TextField()

    # The panels are defined on the viewset

    def __str__(self):
        return self.text


class DraftStateCustomPrimaryKeyModel(DraftStateMixin, RevisionMixin, models.Model):
    custom_id = models.CharField(max_length=255, primary_key=True)
    text = models.TextField()

    panels = [
        FieldPanel("text"),
        FieldPanel("first_published_at"),
        PublishingPanel(),
    ]

    def __str__(self):
        return self.text


register_snippet(DraftStateCustomPrimaryKeyModel)


# Models with PreviewableMixin
class PreviewableModel(PreviewableMixin, ClusterableModel):
    text = models.TextField()
    categories = ParentalManyToManyField(EventCategory, blank=True)

    def __str__(self):
        return self.text

    def get_preview_template(self, request, mode_name):
        return "tests/previewable_model.html"


register_snippet(PreviewableModel)


class CustomPreviewSizesModel(PreviewableMixin, models.Model):
    text = models.TextField()

    @property
    def preview_sizes(self):
        return CUSTOM_PREVIEW_SIZES

    @property
    def default_preview_size(self):
        return "desktop"


register_snippet(CustomPreviewSizesModel)


class MultiPreviewModesModel(PreviewableMixin, RevisionMixin, models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text

    @property
    def preview_modes(self):
        return [("", "Normal"), ("alt#1", "Alternate")]

    @property
    def default_preview_mode(self):
        return "alt#1"

    def get_preview_template(self, request, mode_name):
        templates = {
            "": "tests/previewable_model.html",
            "alt#1": "tests/previewable_model_alt.html",
        }
        return templates.get(mode_name, templates[""])


register_snippet(MultiPreviewModesModel)


class NonPreviewableModel(PreviewableMixin, RevisionMixin, models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text

    preview_modes = []


register_snippet(NonPreviewableModel)


# Models with LockableMixin


class LockableModel(LockableMixin, models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text


register_snippet(LockableModel)


# Models with WorkflowMixin
# Note: do not use Workflow in the model name to avoid incorrect counts in tests
# that look for the word "workflow"


class ModeratedModel(WorkflowMixin, DraftStateMixin, RevisionMixin, models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text


# Snippet with all mixins enabled


class FullFeaturedSnippet(
    PreviewableMixin,
    WorkflowMixin,
    DraftStateMixin,
    LockableMixin,
    RevisionMixin,
    TranslatableMixin,
    index.Indexed,
    models.Model,
):
    class CountryCode(models.TextChoices):
        INDONESIA = "ID"
        PHILIPPINES = "PH"
        UNITED_KINGDOM = "UK"

    text = models.TextField()
    country_code = models.CharField(
        max_length=2,
        choices=CountryCode.choices,
        default=CountryCode.UNITED_KINGDOM,
        blank=True,
    )
    some_date = models.DateField(auto_now=True)
    some_number = models.IntegerField(default=0, blank=True)

    some_attribute = "some value"

    workflow_states = GenericRelation(
        "wagtailcore.WorkflowState",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="full_featured_snippet",
        for_concrete_model=False,
    )

    revisions = GenericRelation(
        "wagtailcore.Revision",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="full_featured_snippet",
        for_concrete_model=False,
    )

    panels = ["text", "country_code", "some_number"]

    search_fields = [
        index.SearchField("text"),
        index.AutocompleteField("text"),
        index.FilterField("text"),
        index.FilterField("country_code"),
    ]

    def __str__(self):
        return self.text

    def modulo_two(self):
        return self.pk % 2

    def tristate(self):
        return (None, True, False)[self.pk % 3]

    def get_preview_template(self, request, mode_name):
        return "tests/previewable_model.html"

    def get_foo_country_code(self):
        return f"Foo {self.country_code}"

    get_foo_country_code.admin_order_field = "country_code"
    get_foo_country_code.short_description = "custom FOO column"

    class Meta(TranslatableMixin.Meta):
        verbose_name = "full-featured snippet"
        verbose_name_plural = "full-featured snippets"


def get_default_advert():
    return Advert.objects.first()


class VariousOnDeleteModel(models.Model):
    text = models.TextField()
    on_delete_cascade = models.ForeignKey(
        Advert, on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    on_delete_protect = models.ForeignKey(
        Advert, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    on_delete_restrict = models.ForeignKey(
        Advert, on_delete=models.RESTRICT, null=True, blank=True, related_name="+"
    )
    on_delete_set_null = models.ForeignKey(
        Advert, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    on_delete_set_default = models.ForeignKey(
        Advert,
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        default=get_default_advert,
        related_name="+",
    )
    on_delete_set = models.ForeignKey(
        Advert,
        on_delete=models.SET(get_default_advert),
        null=True,
        blank=True,
        related_name="+",
    )
    on_delete_do_nothing = models.ForeignKey(
        Advert, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="+"
    )

    protected_image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    protected_document = models.ForeignKey(
        "wagtaildocs.Document",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    protected_page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    protected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    cascading_toy = models.ForeignKey(
        "tests.FeatureCompleteToy",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    stream_field = StreamField(
        [
            (
                "advertisement_content",
                StreamBlock(
                    [
                        (
                            "captioned_advert",
                            StructBlock(
                                [
                                    ("advert", SnippetChooserBlock(Advert)),
                                    ("caption", CharBlock()),
                                ],
                            ),
                        ),
                        ("rich_text", RichTextBlock()),
                    ]
                ),
            ),
            ("image", ImageChooserBlock()),
            ("document", DocumentChooserBlock()),
        ],
    )
    rich_text = RichTextField(blank=True)


class StandardIndex(Page):
    """Index for the site"""

    parent_page_types = [Page]

    # A custom panel setup where all Promote fields are placed in the Content tab instead;
    # we use this to test that the 'promote' tab is left out of the output when empty
    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("seo_title"),
        FieldPanel("slug"),
        InlinePanel("advert_placements", heading="Adverts", label="advert"),
    ]

    promote_panels = []


class PromotionalPage(Page):
    content_panels = Page.content_panels + [
        InlinePanel("advert_placements", heading="Adverts", label="advert", min_num=1),
    ]


class StandardChild(Page):
    pass


# Test overriding edit_handler with a custom one
StandardChild.edit_handler = TabbedInterface(
    [
        ObjectList(StandardChild.content_panels, heading="Content"),
        ObjectList(StandardChild.promote_panels, heading="Promote"),
        ObjectList(StandardChild.settings_panels, heading="Settings"),
        ObjectList(
            [
                HelpPanel("Watch out for asteroids"),
            ],
            heading="Dinosaurs",
        ),
    ],
    base_form_class=WagtailAdminPageForm,
)


class BusinessIndex(Page):
    """Can be placed anywhere, can only have Business children"""

    subpage_types = ["tests.BusinessChild", "tests.BusinessSubIndex"]


class BusinessSubIndex(Page):
    """Can be placed under BusinessIndex, and have BusinessChild children"""

    # BusinessNowherePage is 'incorrectly' added here as a possible child.
    # The rules on BusinessNowherePage prevent it from being a child here though.
    subpage_types = ["tests.BusinessChild", "tests.BusinessNowherePage"]
    parent_page_types = ["tests.BusinessIndex"]


class BusinessChild(Page):
    """Can only be placed under Business indexes, no children allowed"""

    subpage_types = []
    parent_page_types = ["tests.BusinessIndex", BusinessSubIndex]
    page_description = _("A lazy business child page description")


class BusinessNowherePage(Page):
    """Not allowed to be placed anywhere"""

    parent_page_types = []


class CustomCopyFormPage(Page):
    copy_form_class = CustomCopyForm


class TaggedPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "tests.TaggedPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class TaggedPage(Page):
    tags = ClusterTaggableManager(through=TaggedPageTag, blank=True)

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("tags"),
    ]

    # Page.search_fields intentionally omitted to test warning
    search_fields = [
        index.SearchField("tags"),
    ]


class TaggedChildPage(TaggedPage):
    pass


class TaggedGrandchildPage(TaggedChildPage):
    pass


class SingletonPage(Page):
    @classmethod
    def can_create_at(cls, parent):
        # You can only create one of these!
        return super().can_create_at(parent) and not cls.objects.exists()


class SingletonPageViaMaxCount(Page):
    max_count = 1


class PageChooserModel(models.Model):
    page = models.ForeignKey(
        "wagtailcore.Page", help_text="help text", on_delete=models.CASCADE
    )


class EventPageChooserModel(models.Model):
    page = models.ForeignKey(
        "tests.EventPage", help_text="more help text", on_delete=models.CASCADE
    )


class SnippetChooserModel(models.Model):
    advert = models.ForeignKey(Advert, help_text="help text", on_delete=models.CASCADE)
    full_featured = models.ForeignKey(
        FullFeaturedSnippet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Chosen snippet",
    )

    panels = [
        FieldPanel("advert"),
        FieldPanel("full_featured"),
    ]


class SnippetChooserModelWithCustomPrimaryKey(models.Model):
    advertwithcustomprimarykey = models.ForeignKey(
        AdvertWithCustomPrimaryKey, help_text="help text", on_delete=models.CASCADE
    )

    panels = [
        FieldPanel("advertwithcustomprimarykey"),
    ]


class CustomImage(AbstractImage):
    caption = models.CharField(max_length=255, blank=True)
    fancy_caption = RichTextField(blank=True)
    not_editable_field = models.CharField(max_length=255, blank=True)

    admin_form_fields = Image.admin_form_fields + (
        "caption",
        "fancy_caption",
    )

    class Meta:
        unique_together = [("title", "collection")]


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, related_name="renditions", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("image", "filter_spec", "focal_point_key"),
                name="unique_rendition",
            )
        ]


# Custom image model with a required field
class CustomImageWithAuthor(AbstractImage):
    author = models.CharField(max_length=255)

    admin_form_fields = Image.admin_form_fields + ("author",)


class CustomRenditionWithAuthor(AbstractRendition):
    image = models.ForeignKey(
        CustomImageWithAuthor, related_name="renditions", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class CustomDocument(AbstractDocument):
    description = models.TextField(blank=True)
    fancy_description = RichTextField(blank=True)
    admin_form_fields = Document.admin_form_fields + (
        "description",
        "fancy_description",
    )

    class Meta:
        unique_together = [("title", "collection")]


# Custom document model with a required field
class CustomDocumentWithAuthor(AbstractDocument):
    author = models.CharField(max_length=255)

    admin_form_fields = Document.admin_form_fields + ("author",)


class JSONStreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
    )

    class Meta:
        verbose_name = "JSON stream model"


class JSONMinMaxCountStreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        min_num=2,
        max_num=5,
    )


class JSONBlockCountsStreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        block_counts={
            "text": {"min_num": 1},
            "rich_text": {"max_num": 1},
            "image": {"min_num": 1, "max_num": 1},
        },
    )


class ExtendedImageChooserBlock(ImageChooserBlock):
    """
    Example of Block with custom get_api_representation method.
    If the request has an 'extended' query param, it returns a dict of id and title,
    otherwise, it returns the default value.
    """

    def get_api_representation(self, value, context=None):
        image_id = super().get_api_representation(value, context=context)
        if "request" in context and context["request"].query_params.get(
            "extended", False
        ):
            return {"id": image_id, "title": value.title}
        return image_id


class StreamPage(Page):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ExtendedImageChooserBlock()),
            (
                "product",
                StructBlock(
                    [
                        ("name", CharBlock()),
                        ("price", CharBlock()),
                    ]
                ),
            ),
            ("raw_html", RawHTMLBlock()),
            (
                "books",
                StreamBlock(
                    [
                        ("title", CharBlock()),
                        ("author", CharBlock()),
                    ]
                ),
            ),
            (
                "title_list",
                ListBlock(CharBlock()),
            ),
            ("image_with_alt", ImageBlock()),
        ],
    )

    api_fields = ("body",)

    content_panels = [
        TitleFieldPanel("title"),
        FieldPanel("body"),
    ]

    preview_modes = []


class DefaultStreamPage(Page):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        default="",
    )

    content_panels = [
        TitleFieldPanel("title"),
        FieldPanel("body"),
    ]


class ComplexDefaultStreamPage(Page):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            (
                "books",
                StreamBlock(
                    [
                        ("title", CharBlock()),
                        ("author", CharBlock()),
                    ]
                ),
            ),
        ],
        default=[
            ("rich_text", "<p>My <i>lovely</i> books</p>"),
            (
                "books",
                [("title", "The Great Gatsby"), ("author", "F. Scott Fitzgerald")],
            ),
        ],
    )

    content_panels = [
        TitleFieldPanel("title"),
        FieldPanel("body"),
    ]


class MTIBasePage(Page):
    is_creatable = False

    class Meta:
        verbose_name = "MTI base page"


class MTIChildPage(MTIBasePage):
    # Should be creatable by default, no need to set anything
    pass


class NoCreatableSubpageTypesPage(Page):
    subpage_types = [MTIBasePage]


class NoSubpageTypesPage(Page):
    subpage_types = []


class AbstractPage(Page):
    class Meta:
        abstract = True


@register_setting
class TestSiteSetting(BaseSiteSetting):
    title = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)


@register_setting
class TestGenericSetting(BaseGenericSetting):
    title = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)


@register_setting
class TestPermissionedGenericSetting(BaseGenericSetting):
    title = models.CharField(max_length=100)
    sensitive_email = models.EmailField(max_length=50)

    panels = [
        FieldPanel("title"),
        FieldPanel(
            "sensitive_email",
            permission="tests.can_edit_sensitive_email_generic_setting",
        ),
    ]

    class Meta:
        permissions = [
            (
                "can_edit_sensitive_email_generic_setting",
                "Can edit sensitive email generic setting.",
            ),
        ]


@register_setting
class TestPermissionedSiteSetting(BaseSiteSetting):
    title = models.CharField(max_length=100)
    sensitive_email = models.EmailField(max_length=50)

    panels = [
        FieldPanel("title"),
        FieldPanel(
            "sensitive_email", permission="tests.can_edit_sensitive_email_site_setting"
        ),
    ]

    class Meta:
        permissions = [
            (
                "can_edit_sensitive_email_site_setting",
                "Can edit sensitive email site setting.",
            ),
        ]


@register_setting
class ImportantPagesSiteSetting(BaseSiteSetting):
    sign_up_page = models.ForeignKey(
        "wagtailcore.Page", related_name="+", null=True, on_delete=models.SET_NULL
    )
    general_terms_page = models.ForeignKey(
        "wagtailcore.Page", related_name="+", null=True, on_delete=models.SET_NULL
    )
    privacy_policy_page = models.ForeignKey(
        "wagtailcore.Page", related_name="+", null=True, on_delete=models.SET_NULL
    )


@register_setting(name="important-pages-generic-setting")
class ImportantPagesGenericSetting(BaseGenericSetting):
    sign_up_page = models.ForeignKey(
        "wagtailcore.Page", related_name="+", null=True, on_delete=models.SET_NULL
    )
    general_terms_page = models.ForeignKey(
        "wagtailcore.Page", related_name="+", null=True, on_delete=models.SET_NULL
    )
    privacy_policy_page = models.ForeignKey(
        "wagtailcore.Page", related_name="+", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _("important pages settings")
        verbose_name_plural = _("important pages settings")


@register_setting(icon="tag")
class IconSiteSetting(BaseSiteSetting):
    pass


@register_setting(icon="tag")
class IconGenericSetting(BaseGenericSetting):
    pass


@register_setting
class FileSiteSetting(BaseSiteSetting):
    file = models.FileField()


@register_setting
class FileGenericSetting(BaseGenericSetting):
    file = models.FileField()


@register_setting
class PreviewableSiteSetting(PreviewableMixin, BaseSiteSetting):
    text = models.TextField()

    def get_preview_template(self, request, mode_name):
        return "tests/previewable_setting.html"


@register_setting
class PreviewableGenericSetting(PreviewableMixin, BaseGenericSetting):
    text = models.TextField()

    def get_preview_template(self, request, mode_name):
        return "tests/previewable_setting.html"


class BlogCategory(models.Model):
    name = models.CharField(unique=True, max_length=80)


class BlogCategoryBlogPage(models.Model):
    category = models.ForeignKey(
        BlogCategory, related_name="+", on_delete=models.CASCADE
    )
    page = ParentalKey(
        "ManyToManyBlogPage", related_name="categories", on_delete=models.CASCADE
    )
    panels = [
        FieldPanel("category"),
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
        BlogCategory, through=BlogCategoryBlogPage, blank=True
    )

    # make first_published_at editable on this page model
    settings_panels = Page.settings_panels + [
        FieldPanel("first_published_at"),
    ]


class OneToOnePage(Page):
    """
    A Page containing a O2O relation.
    """

    body = RichTextBlock(blank=True)
    page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name="+", on_delete=models.CASCADE
    )


class GenericSnippetPage(Page):
    """
    A page containing a reference to an arbitrary snippet (or any model for that matter)
    linked by a GenericForeignKey
    """

    snippet_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    snippet_object_id = models.PositiveIntegerField(null=True, blank=True)
    snippet_content_object = GenericForeignKey(
        "snippet_content_type", "snippet_object_id"
    )


class CustomImageFilePath(AbstractImage):
    def get_upload_to(self, filename):
        """Create a path that's file-system friendly.

        By hashing the file's contents we guarantee an equal distribution
        of files within our root directories. This also gives us a
        better chance of uploading images with the same filename, but
        different contents - this isn't guaranteed as we're only using
        the first three characters of the checksum.
        """
        original_filepath = super().get_upload_to(filename)
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


class CustomPageQuerySet(PageQuerySet):
    def about_spam(self):
        return self.filter(title__contains="spam")


CustomManager = PageManager.from_queryset(CustomPageQuerySet)


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
        FieldPanel("foo"),
    ]


class DefaultRichTextFieldPage(Page):
    body = RichTextField()

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


class DefaultRichBlockFieldPage(Page):
    body = StreamField(
        [
            ("rich_text", RichTextBlock()),
        ],
    )

    content_panels = Page.content_panels + [FieldPanel("body")]


class CustomRichTextFieldPage(Page):
    body = RichTextField(editor="custom")

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


class CustomRichBlockFieldPage(Page):
    body = StreamField(
        [
            ("rich_text", RichTextBlock(editor="custom")),
        ],
    )

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


class RichTextFieldWithFeaturesPage(Page):
    body = RichTextField(features=["quotation", "embed", "made-up-feature"])

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


# a page that only contains RichTextField within an InlinePanel,
# to test that the inline child's form media gets pulled through
class SectionedRichTextPageSection(Orderable):
    page = ParentalKey(
        "tests.SectionedRichTextPage", related_name="sections", on_delete=models.CASCADE
    )
    body = RichTextField()

    panels = [FieldPanel("body")]


class SectionedRichTextPage(Page):
    content_panels = [
        TitleFieldPanel("title", classname="title"),
        InlinePanel("sections"),
    ]


class InlineStreamPageSection(Orderable):
    page = ParentalKey(
        "tests.InlineStreamPage", related_name="sections", on_delete=models.CASCADE
    )
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
    )
    panels = [FieldPanel("body")]


class InlineStreamPage(Page):
    content_panels = [
        TitleFieldPanel("title", classname="title"),
        InlinePanel("sections"),
    ]


class TableBlockStreamPage(Page):
    table = StreamField([("table", TableBlock())])

    content_panels = [FieldPanel("table")]


class UserProfile(models.Model):
    # Wagtail's schema must be able to coexist alongside a custom UserProfile model
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    favourite_colour = models.CharField(max_length=255)


class PanelSiteSettings(TestSiteSetting):
    panels = [FieldPanel("title")]


class PanelGenericSettings(TestGenericSetting):
    panels = [FieldPanel("title")]


class TabbedSiteSettings(TestSiteSetting):
    edit_handler = TabbedInterface(
        [
            ObjectList([FieldPanel("title")], heading="First tab"),
            ObjectList([FieldPanel("email")], heading="Second tab"),
        ]
    )


class TabbedGenericSettings(TestGenericSetting):
    edit_handler = TabbedInterface(
        [
            ObjectList([FieldPanel("title")], heading="First tab"),
            ObjectList([FieldPanel("email")], heading="Second tab"),
        ]
    )


class AlwaysShowInMenusPage(Page):
    show_in_menus_default = True


# test for AddField migrations on StreamFields using various default values
class AddedStreamFieldWithoutDefaultPage(Page):
    body = StreamField([("title", CharBlock())])


class AddedStreamFieldWithEmptyStringDefaultPage(Page):
    body = StreamField([("title", CharBlock())], default="")


class AddedStreamFieldWithEmptyListDefaultPage(Page):
    body = StreamField([("title", CharBlock())], default=[])


class SecretPage(Page):
    boring_data = models.TextField()
    secret_data = models.TextField()

    content_panels = Page.content_panels + [
        FieldPanel("boring_data"),
        FieldPanel("secret_data", permission="superuser"),
    ]


class SimpleParentPage(Page):
    subpage_types = ["tests.SimpleChildPage"]


class SimpleChildPage(Page):
    parent_page_types = ["tests.SimpleParentPage"]

    max_count_per_parent = 1


class PersonPage(Page):
    first_name = models.CharField(
        max_length=255,
        verbose_name="First Name",
    )
    last_name = models.CharField(
        max_length=255,
        verbose_name="Last Name",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                "first_name",
                "last_name",
            ],
            "Person",
        ),
        "addresses",
        "social_links",
    ]

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "persons"


class Address(index.Indexed, ClusterableModel, Orderable):
    address = models.CharField(
        max_length=255,
        verbose_name="Address",
    )
    tags = ClusterTaggableManager(
        through="tests.AddressTag",
        blank=True,
    )
    person = ParentalKey(
        to="tests.PersonPage", related_name="addresses", verbose_name="Person"
    )

    panels = [
        FieldPanel("address"),
        FieldPanel("tags"),
    ]

    class Meta:
        verbose_name = "address"
        verbose_name_plural = "addresses"


class AddressTag(TaggedItemBase):
    content_object = ParentalKey(
        to="tests.Address", on_delete=models.CASCADE, related_name="tagged_items"
    )


class SocialLink(index.Indexed, ClusterableModel):
    url = models.URLField()
    kind = models.CharField(
        max_length=30,
        choices=[
            ("twitter", "Twitter"),
            ("facebook", "Facebook"),
        ],
    )
    person = ParentalKey(
        to="tests.PersonPage", related_name="social_links", verbose_name="Person"
    )

    panels = ["url", "kind"]

    class Meta:
        verbose_name = "social link"
        verbose_name_plural = "social links"


class RestaurantPage(Page):
    tags = ClusterTaggableManager(through="tests.TaggedRestaurant", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("tags"),
    ]


class RestaurantTag(TagBase):
    free_tagging = False

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"


class TaggedRestaurant(ItemBase):
    tag = models.ForeignKey(
        RestaurantTag, related_name="tagged_restaurants", on_delete=models.CASCADE
    )
    content_object = ParentalKey(
        to="tests.RestaurantPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


class SimpleTask(Task):
    pass


class UserApprovalTaskState(TaskState):
    pass


class UserApprovalTask(Task):
    """
    Based on https://docs.wagtail.org/en/stable/extending/custom_tasks.html.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False
    )

    admin_form_fields = Task.admin_form_fields + ["user"]

    task_state_class = UserApprovalTaskState

    # prevent editing of `user` after the task is created
    # by default, this attribute contains the 'name' field to prevent tasks from being renamed
    admin_form_readonly_on_edit_fields = Task.admin_form_readonly_on_edit_fields + [
        "user"
    ]

    def user_can_access_editor(self, page, user):
        return user == self.user

    def page_locked_for_user(self, page, user):
        return user != self.user

    def get_actions(self, page, user):
        if user == self.user:
            return [
                ("approve", "Approve", False),
                ("approve", "Approve with style", True),
                ("reject", "Reject", False),
                ("cancel", "Cancel", False),
            ]
        else:
            return []

    def get_template_for_action(self, action):
        # https://github.com/wagtail/wagtail/issues/12222
        # This will be used for "Approve with style" which has the third value
        # (action_requires_additional_data_from_modal) set to True.
        if action == "approve":
            return "tests/workflows/approve_with_style.html"
        return super().get_template_for_action(action)

    def on_action(self, task_state, user, action_name, **kwargs):
        if action_name == "cancel":
            return task_state.workflow_state.cancel(user=user)
        else:
            return super().on_action(task_state, user, action_name, **kwargs)

    def get_task_states_user_can_moderate(self, user, **kwargs):
        if user == self.user:
            # get all task states linked to the (base class of) current task
            return TaskState.objects.filter(
                status=TaskState.STATUS_IN_PROGRESS, task=self.task_ptr
            )
        else:
            return TaskState.objects.none()

    @classmethod
    def get_description(cls):
        return "Only a specific user can approve this task"


# StreamField media definitions must not be evaluated at startup (e.g. during system checks) -
# these may fail if e.g. ManifestStaticFilesStorage is in use and collectstatic has not been run.
# Check this with a media definition that deliberately errors; if media handling is not set up
# correctly, then the mere presence of this model definition will cause startup to fail.
class DeadlyTextInput(forms.TextInput):
    @property
    def media(self):
        raise Exception("BOOM! Attempted to evaluate DeadlyTextInput.media")


class DeadlyCharBlock(FieldBlock):
    def __init__(self, *args, **kwargs):
        self.field = forms.CharField(widget=DeadlyTextInput())
        super().__init__(*args, **kwargs)


class DeadlyStreamPage(Page):
    body = StreamField(
        [
            ("title", DeadlyCharBlock()),
        ],
    )
    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]


# Check that get_image_model and get_document_model work at import time
# (so that it's possible to use them in foreign key definitions, for example)
ReimportedImageModel = get_image_model()
ReimportedDocumentModel = get_document_model()


# Custom document model with a custom tag field
class TaggedRestaurantDocument(ItemBase):
    tag = models.ForeignKey(
        RestaurantTag, related_name="tagged_documents", on_delete=models.CASCADE
    )
    content_object = models.ForeignKey(
        to="tests.CustomRestaurantDocument",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


class CustomRestaurantDocument(AbstractDocument):
    tags = TaggableManager(
        help_text=None,
        blank=True,
        verbose_name="tags",
        through=TaggedRestaurantDocument,
    )
    admin_form_fields = Document.admin_form_fields


# Custom image model with a custom tag field
class TaggedRestaurantImage(ItemBase):
    tag = models.ForeignKey(
        RestaurantTag, related_name="tagged_images", on_delete=models.CASCADE
    )
    content_object = models.ForeignKey(
        to="tests.CustomRestaurantImage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


class CustomRestaurantImage(AbstractImage):
    tags = TaggableManager(
        help_text=None, blank=True, verbose_name="tags", through=TaggedRestaurantImage
    )
    admin_form_fields = Image.admin_form_fields


class ModelWithStringTypePrimaryKey(models.Model):
    """
    This model intentionally uses `CharField` as a primary key for testing purpose.
    """

    custom_id = models.CharField(max_length=255, primary_key=True)
    content = models.CharField(max_length=255)


class ModelWithNullableParentalKey(models.Model):
    """
    There's not really a valid use case for null parental keys, but their presence should not
    break things outright (e.g. when determining the object ID to store things under in the
    references index).
    """

    page = ParentalKey(Page, blank=True, null=True)
    content = RichTextField()


class GalleryPage(Page):
    content_panels = Page.content_panels + [
        MultipleChooserPanel(
            "gallery_images", heading="Gallery images", chooser_field_name="image"
        )
    ]


class GalleryPageImage(Orderable):
    page = ParentalKey(
        "tests.GalleryPage", related_name="gallery_images", on_delete=models.CASCADE
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )


class GenericSnippetNoIndexPage(GenericSnippetPage):
    wagtail_reference_index_ignore = True


class GenericSnippetNoFieldIndexPage(GenericSnippetPage):
    snippet_content_type_nonindexed = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    snippet_content_type_nonindexed.wagtail_reference_index_ignore = True


def random_quotable_pk():
    quote_chrs = '":/_#?;@&=+$,"[]<>%\n\\'
    components = (quote_chrs, string.ascii_letters, string.digits)
    return "".join(random.choice(components[i % len(components)]) for i in range(10))


# Models to be registered with a ModelViewSet
class FeatureCompleteToy(index.Indexed, models.Model):
    strid = models.CharField(
        max_length=255,
        primary_key=True,
        default=random_quotable_pk,
    )
    name = models.CharField(max_length=255)
    release_date = models.DateField(default=datetime.date.today)

    search_fields = [
        index.SearchField("name"),
        index.AutocompleteField("name"),
        index.FilterField("name"),
        index.FilterField("release_date"),
    ]

    def is_cool(self):
        if self.name == self.name[::-1]:
            return True
        if (lowered := self.name.lower()) == lowered[::-1]:
            return None
        return False

    def __str__(self):
        return f"{self.name} ({self.release_date})"

    class Meta:
        permissions = [("can_set_release_date", "Can set release date")]


class PurgeRevisionsProtectedTestModel(models.Model):
    revision = models.OneToOneField(
        "wagtailcore.Revision", on_delete=models.PROTECT, related_name="+"
    )


class SearchTestModel(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    panels = [
        FieldPanel("title"),
        FieldPanel("body"),
    ]

    def __str__(self):
        return self.title


class CustomPermissionTester(PagePermissionTester):
    def can_view_revisions(self):
        return False


class CustomPermissionPage(Page):
    def permissions_for_user(self, user):
        return CustomPermissionTester(user, self)


class CustomPermissionModel(models.Model):
    text = models.TextField(default="Tailwag")

    class Meta:
        verbose_name = "ADVANCED permission model"
        verbose_name_plural = "ADVANCED permission models"

        # Django's default_permissions are ("add", "change", "delete", "view").
        # Django will generate permissions for each of these actions with the
        # format f"{action}_{model_name}" and the label "Can {action} {verbose_name}".
        # This means if the action is "bulk_update", the codename will be
        # "bulk_update_custompermissionmodel" and the label will be
        # "Can bulk_update ADVANCED permission model".
        # See https://github.com/django/django/blob/stable/5.0.x/django/contrib/auth/management/__init__.py#L22-L35
        default_permissions = ("add", "change", "delete", "view", "bulk_update")

        # Permissions with completely custom codenames and labels
        permissions = [
            # Starts with can_ and "Can "
            ("can_start_trouble", "Can start trouble"),
            # Doesn't start with can_ and "Can "
            ("cause_chaos", "Cause chaos for advanced permission model"),
            # Starts with an action similar to a built-in permission "change_"
            ("change_text", "Change text"),
            # Without any _ and the label ends with the default verbose_name
            ("control", "Manage custom permission model"),
        ]


register_snippet(CustomPermissionModel)


class RequiredDatePage(Page):
    deadline = models.DateField()

    content_panels = [
        TitleFieldPanel("title", classname="title"),
        FieldPanel("deadline"),
    ]
