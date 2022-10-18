import hashlib
import os
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

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.mail import send_mail
from wagtail.admin.panels import (
    FieldPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    PublishingPanel,
    TabbedInterface,
)
from wagtail.blocks import (
    CharBlock,
    FieldBlock,
    RawHTMLBlock,
    RichTextBlock,
    StreamBlock,
    StructBlock,
)
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import (
    FORM_FIELD_CHOICES,
    AbstractEmailForm,
    AbstractFormField,
    AbstractFormSubmission,
)
from wagtail.contrib.forms.views import SubmissionsListView
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.contrib.sitemaps import Sitemap
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.documents import get_document_model
from wagtail.documents.models import AbstractDocument, Document
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import AbstractImage, AbstractRendition, Image
from wagtail.models import (
    DraftStateMixin,
    Orderable,
    Page,
    PageManager,
    PageQuerySet,
    PreviewableMixin,
    RevisionMixin,
    Task,
    TranslatableMixin,
)
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .forms import FormClassAdditionalFieldPageForm, ValidatedPageForm

EVENT_AUDIENCE_CHOICES = (
    ("public", "Public"),
    ("private", "Private"),
)


COMMON_PANELS = (
    FieldPanel("slug"),
    FieldPanel("seo_title"),
    FieldPanel("show_in_menus"),
    FieldPanel("search_description"),
)


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
        FieldPanel("image"),
        FieldPanel("embed_url"),
        FieldPanel("caption"),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links


class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel("title"),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Simple page
class SimplePage(Page):
    content = models.TextField()
    page_description = "A simple page description"

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("content"),
    ]

    def get_admin_display_title(self):
        return "%s (simple page)" % super().get_admin_display_title()


class MultiPreviewModesPage(Page):
    template = "tests/simple_page.html"

    @property
    def preview_modes(self):
        return [("original", "Original"), ("alt#1", "Alternate")]

    @property
    def default_preview_mode(self):
        return "alt#1"

    def get_preview_template(self, request, mode_name):
        if mode_name == "alt#1":
            return "tests/simple_page_alt.html"
        return super().get_preview_template(request, mode_name)


# Page with Excluded Fields when copied
class PageWithExcludedCopyField(Page):
    content = models.TextField()

    # Exclude this field from being copied
    special_field = models.CharField(blank=True, max_length=255, default="Very Special")
    exclude_fields_in_copy = ["special_field"]

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("special_field"),
        FieldPanel("content"),
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
        FieldPanel("title", classname="title"),
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

    panels = [
        FieldPanel("name"),
        FieldPanel("date_awarded"),
    ]

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
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("image"),
        MultiFieldPanel(LinkFields.panels, "Link"),
        InlinePanel("awards", label="Awards"),
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
        start_date = cleaned_data["date_from"]
        end_date = cleaned_data["date_to"]
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

    search_fields = [
        index.SearchField("get_audience_display"),
        index.SearchField("location"),
        index.SearchField("body"),
        index.FilterField("url_path"),
    ]

    password_required_template = "tests/event_page_password_required.html"
    base_form_class = EventPageForm

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("date_from"),
        FieldPanel("date_to"),
        FieldPanel("time_from"),
        FieldPanel("time_to"),
        FieldPanel("location"),
        FieldPanel("audience", help_text="Who this event is for"),
        FieldPanel("cost"),
        FieldPanel("signup_link"),
        InlinePanel("carousel_items", label="Carousel items"),
        FieldPanel("body"),
        InlinePanel(
            "speakers",
            label="Speakers",
            heading="Speaker lineup",
            help_text="Put the keynote speaker first",
        ),
        InlinePanel("related_links", label="Related links"),
        FieldPanel("categories"),
        # InlinePanel related model uses `pk` not `id`
        InlinePanel("head_counts", label="Head Counts"),
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
    head_count = models.IntegerField()
    panels = [FieldPanel("head_count")]


# Override the standard WagtailAdminPageForm to add field that is not in model
# so that we can test additional potential issues like comparing versions
class FormClassAdditionalFieldPage(Page):
    location = models.CharField(max_length=255)
    body = RichTextField(blank=True)

    content_panels = [
        FieldPanel("title", classname="title"),
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

    def get_static_site_paths(self):
        # Get page count
        page_count = self.get_paginator().num_pages

        # Yield a path for each page
        for page in range(page_count):
            yield "/%d/" % (page + 1)

        # Yield from superclass
        for path in super().get_static_site_paths():
            yield path

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
        FieldPanel("title", classname="title"),
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
    # https://docs.wagtail.org/en/stable/reference/contrib/forms/customisation.html#customise-form-submissions-listing-in-wagtail-admin
    # works without triggering circular dependency issues -
    # see https://github.com/wagtail/wagtail/issues/6265
    submissions_list_view_class = SubmissionsListView

    content_panels = [
        FieldPanel("title", classname="title"),
        InlinePanel("form_fields", label="Form fields"),
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("from_address"),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]


# FormPage with a non-HTML extension


class JadeFormField(AbstractFormField):
    page = ParentalKey(
        "JadeFormPage", related_name="form_fields", on_delete=models.CASCADE
    )


class JadeFormPage(AbstractEmailForm):
    template = "tests/form_page.jade"

    content_panels = [
        FieldPanel("title", classname="title"),
        InlinePanel("form_fields", label="Form fields"),
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
        context = super(FormPageWithRedirect, self).get_context(request)
        context["greeting"] = "hello world"
        return context

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        """
        Renders the landing page OR if a receipt_page_redirect is chosen redirects to this page.
        """
        if self.thank_you_redirect_page:
            return redirect(self.thank_you_redirect_page.url, permanent=False)

        return super(FormPageWithRedirect, self).render_landing_page(
            request, form_submission, *args, **kwargs
        )

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("thank_you_redirect_page"),
        InlinePanel("form_fields", label="Form fields"),
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
        FieldPanel("title", classname="title"),
        FieldPanel("intro"),
        InlinePanel("custom_form_fields", label="Form fields"),
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
        FieldPanel("title", classname="title"),
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Form fields"),
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


class FormPageWithCustomFormBuilder(AbstractEmailForm):
    """
    A Form page that has a custom form builder and uses a custom
    form field model with additional field_type choices.
    """

    form_builder = CustomFormBuilder

    content_panels = [
        FieldPanel("title", classname="title"),
        InlinePanel("form_fields", label="Form fields"),
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


class AdvertWithCustomUUIDPrimaryKey(ClusterableModel):
    advert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel("url"),
        FieldPanel("text"),
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


# Models with RevisionMixin
class RevisableModel(RevisionMixin, models.Model):
    text = models.TextField()


register_snippet(RevisableModel)


class RevisableChildModel(RevisableModel):
    secret_text = models.TextField(blank=True, default="")

    panels = [
        FieldPanel("text"),
        FieldPanel("secret_text", permission="superuser"),
    ]


register_snippet(RevisableChildModel)


class RevisableGrandChildModel(RevisableChildModel):
    pass


# Models with DraftStateMixin
class DraftStateModel(DraftStateMixin, RevisionMixin, models.Model):
    text = models.TextField()

    panels = [
        FieldPanel("text"),
        PublishingPanel(),
    ]

    def __str__(self):
        return self.text


register_snippet(DraftStateModel)


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


class StandardIndex(Page):
    """Index for the site"""

    parent_page_types = [Page]

    # A custom panel setup where all Promote fields are placed in the Content tab instead;
    # we use this to test that the 'promote' tab is left out of the output when empty
    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("seo_title"),
        FieldPanel("slug"),
        InlinePanel("advert_placements", label="Adverts"),
    ]

    promote_panels = []


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
    parent_page_types = ["tests.BusinessIndex", "tests.BusinessChild"]


class BusinessChild(Page):
    """Can only be placed under Business indexes, no children allowed"""

    subpage_types = []
    parent_page_types = ["tests.BusinessIndex", BusinessSubIndex]
    page_description = _("A lazy business child page description")


class BusinessNowherePage(Page):
    """Not allowed to be placed anywhere"""

    parent_page_types = []


class TaggedPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "tests.TaggedPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class TaggedPage(Page):
    tags = ClusterTaggableManager(through=TaggedPageTag, blank=True)

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("tags"),
    ]


class TaggedChildPage(TaggedPage):
    pass


class TaggedGrandchildPage(TaggedChildPage):
    pass


class SingletonPage(Page):
    @classmethod
    def can_create_at(cls, parent):
        # You can only create one of these!
        return (
            super(SingletonPage, cls).can_create_at(parent) and not cls.objects.exists()
        )


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

    panels = [
        FieldPanel("advert"),
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
        unique_together = (("image", "filter_spec", "focal_point_key"),)


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


class StreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        use_json_field=False,
    )


class JSONStreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        use_json_field=True,
    )


class MinMaxCountStreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        min_num=2,
        max_num=5,
        use_json_field=False,
    )


class JSONMinMaxCountStreamModel(models.Model):
    body = StreamField(
        [
            ("text", CharBlock()),
            ("rich_text", RichTextBlock()),
            ("image", ImageChooserBlock()),
        ],
        min_num=2,
        max_num=5,
        use_json_field=True,
    )


class BlockCountsStreamModel(models.Model):
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
        use_json_field=False,
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
        use_json_field=True,
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
        ],
        use_json_field=False,
    )

    api_fields = ("body",)

    content_panels = [
        FieldPanel("title"),
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
        use_json_field=False,
    )

    content_panels = [
        FieldPanel("title"),
        FieldPanel("body"),
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
class TestSiteSetting(BaseSiteSetting):
    title = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)


@register_setting
class TestGenericSetting(BaseGenericSetting):
    title = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)


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


@register_setting
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


@register_setting(icon="icon-setting-tag")
class IconSiteSetting(BaseSiteSetting):
    pass


@register_setting(icon="icon-setting-tag")
class IconGenericSetting(BaseGenericSetting):
    pass


class NotYetRegisteredSiteSetting(BaseSiteSetting):
    pass


class NotYetRegisteredGenericSetting(BaseGenericSetting):
    pass


@register_setting
class FileSiteSetting(BaseSiteSetting):
    file = models.FileField()


@register_setting
class FileGenericSetting(BaseGenericSetting):
    file = models.FileField()


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
        ContentType, on_delete=models.SET_NULL, null=True
    )
    snippet_object_id = models.PositiveIntegerField(null=True)
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
        FieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


class DefaultRichBlockFieldPage(Page):
    body = StreamField(
        [
            ("rich_text", RichTextBlock()),
        ],
        use_json_field=False,
    )

    content_panels = Page.content_panels + [FieldPanel("body")]


class CustomRichTextFieldPage(Page):
    body = RichTextField(editor="custom")

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


class CustomRichBlockFieldPage(Page):
    body = StreamField(
        [
            ("rich_text", RichTextBlock(editor="custom")),
        ],
        use_json_field=False,
    )

    content_panels = [
        FieldPanel("title", classname="title"),
        FieldPanel("body"),
    ]


class RichTextFieldWithFeaturesPage(Page):
    body = RichTextField(features=["quotation", "embed", "made-up-feature"])

    content_panels = [
        FieldPanel("title", classname="title"),
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
        FieldPanel("title", classname="title"),
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
        use_json_field=False,
    )
    panels = [FieldPanel("body")]


class InlineStreamPage(Page):
    content_panels = [
        FieldPanel("title", classname="title"),
        InlinePanel("sections"),
    ]


class TableBlockStreamPage(Page):
    table = StreamField([("table", TableBlock())], use_json_field=False)

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
    body = StreamField([("title", CharBlock())], use_json_field=False)


class AddedStreamFieldWithEmptyStringDefaultPage(Page):
    body = StreamField([("title", CharBlock())], default="", use_json_field=False)


class AddedStreamFieldWithEmptyListDefaultPage(Page):
    body = StreamField([("title", CharBlock())], default=[], use_json_field=False)


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
                FieldPanel("first_name"),
                FieldPanel("last_name"),
            ],
            "Person",
        ),
        InlinePanel("addresses", label="Address"),
    ]

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "Persons"


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
        verbose_name = "Address"
        verbose_name_plural = "Addresses"


class AddressTag(TaggedItemBase):
    content_object = ParentalKey(
        to="tests.Address", on_delete=models.CASCADE, related_name="tagged_items"
    )


class RestaurantPage(Page):
    tags = ClusterTaggableManager(through="tests.TaggedRestaurant", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("tags"),
    ]


class RestaurantTag(TagBase):
    free_tagging = False

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class TaggedRestaurant(ItemBase):
    tag = models.ForeignKey(
        RestaurantTag, related_name="tagged_restaurants", on_delete=models.CASCADE
    )
    content_object = ParentalKey(
        to="tests.RestaurantPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


class SimpleTask(Task):
    pass


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
        use_json_field=False,
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
