from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import TranslatableMixin
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .forms import FancySnippetForm

# AlphaSnippet and ZuluSnippet are for testing ordering of
# snippets when registering.  They are named as such to ensure
# their ordering is clear.  They are registered during testing
# to ensure specific [in]correct register ordering


# AlphaSnippet is registered during TestSnippetOrdering
class AlphaSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


# ZuluSnippet is registered during TestSnippetOrdering
class ZuluSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


# Register model as snippet using register_snippet as both a function and a decorator


class RegisterFunction(models.Model):
    pass


register_snippet(RegisterFunction)


@register_snippet
class RegisterDecorator(models.Model):
    pass


# A snippet model that inherits from index.Indexed can be searched on


@register_snippet
class SearchableSnippet(index.Indexed, models.Model):
    text = models.CharField(max_length=255)

    search_fields = [
        index.SearchField("text"),
        index.AutocompleteField("text"),
    ]

    def __str__(self):
        return self.text


class FilterableSnippet(index.Indexed, models.Model):
    class CountryCode(models.TextChoices):
        INDONESIA = "ID"
        PHILIPPINES = "PH"
        UNITED_KINGDOM = "UK"

    text = models.CharField(max_length=255)
    country_code = models.CharField(max_length=2, choices=CountryCode.choices)

    search_fields = [
        index.SearchField("text"),
        index.FilterField("country_code"),
    ]

    def __str__(self):
        return self.text

    def get_foo_country_code(self):
        return f"Foo {self.country_code}"

    get_foo_country_code.admin_order_field = "country_code"
    get_foo_country_code.short_description = "Custom foo column"


class FilterableSnippetFilterSet(WagtailFilterSet):
    class Meta:
        model = FilterableSnippet
        fields = ["country_code"]


@register_snippet
class StandardSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


@register_snippet
class FancySnippet(models.Model):
    base_form_class = FancySnippetForm


@register_snippet
class FileUploadSnippet(models.Model):
    file = models.FileField()


class RichTextSection(models.Model):
    snippet = ParentalKey(
        "MultiSectionRichTextSnippet", related_name="sections", on_delete=models.CASCADE
    )
    body = RichTextField()

    panels = [
        FieldPanel("body"),
    ]


@register_snippet
class MultiSectionRichTextSnippet(ClusterableModel):
    panels = [
        InlinePanel("sections"),
    ]


@register_snippet
class StandardSnippetWithCustomPrimaryKey(models.Model):
    snippet_id = models.CharField(max_length=255, primary_key=True)
    text = models.CharField(max_length=255)


@register_snippet
class TranslatableSnippet(TranslatableMixin, models.Model):
    text = models.CharField(max_length=255)
