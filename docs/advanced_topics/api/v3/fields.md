(api_v3_fields)=

# Configuring fields

Each model controls which of its fields the v3 API reads and writes through an `api_fields` attribute. This works the same way for pages, snippets, and custom image and document models.

Pages, images, and documents always include a set of built-in fields, such as a page's `title` and `slug`, or an image's `title`, `width`, and `height`. Fields you add to `api_fields` are exposed in addition to these. A snippet only includes its primary key and `meta` by default, so a snippet model must declare at least one entry in `api_fields` to be exposed through the API at all.

## Declaring fields

Define `api_fields` on the model as a list of field names, or `APIField` instances for more control:

```python
from django.db import models
from modelcluster.fields import ParentalKey

from wagtail.api import APIField
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet


class BlogPageAuthor(Orderable):
    page = ParentalKey(
        "blog.BlogPage",
        on_delete=models.CASCADE,
        related_name="authors",
    )
    name = models.CharField(max_length=255)

    api_fields = [
        APIField("name", writable=True),
    ]


class BlogPage(Page):
    published_date = models.DateField()
    intro = RichTextField()
    body = StreamField([...])
    feed_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL
    )
    view_count = models.PositiveIntegerField(default=0)

    api_fields = [
        APIField("published_date", writable=True),
        APIField("intro", writable=True),
        APIField("body", writable=True),
        APIField("feed_image", writable=True),
        APIField("authors", writable=True),
        "view_count",
    ]


@register_snippet
class Advert(models.Model):
    url = models.URLField(blank=True)
    text = models.CharField(max_length=255)

    api_fields = [
        APIField("url", writable=True),
        APIField("text", writable=True),
    ]
```

With this configuration, the API returns all of `BlogPage`'s listed fields, and accepts all of them except `view_count` when creating or editing a page. The `Advert` snippet model is exposed at `/snippets/blog.Advert/` with both of its fields readable and writable.

You can confirm the result for any model using [schema discovery](api_v3_schema).

## Readable fields

Every entry in `api_fields` is readable. An entry can name:

-   a model field, including `RichTextField`, `StreamField`, `ForeignKey`, `ParentalManyToManyField`, and tag fields;
-   a child relation, using the `related_name` of a `ParentalKey`, as described in [](api_v3_child_relations);
-   any other attribute of the model, such as a property, returned as-is and typed as any value in the schema.

The way each field type is represented is covered in [](api_v3_streamfield) and [](api_v3_rich_text).

## Writable fields

An entry is writable only if:

-   it's declared as `APIField(..., writable=True)`. Plain string entries are always read-only;
-   it names a real, editable model field or child relation. Properties and other attributes are always read-only, even when marked as writable;
-   it doesn't use a `serializer`.

A writable child relation also requires the child model to declare at least one writable field of its own in its `api_fields`. Otherwise, Wagtail raises an `ImproperlyConfigured` error when generating the schema.

Writable fields are validated by the same form the admin uses, built from the model's panels, so model and form validation still applies. A writable field doesn't have to appear in a panel to be written through the API.

## Custom serializers

The `serializer` argument changes how a field is read, for example to return an image rendition instead of the image itself (see [](api_v3_images)). Fields with a `serializer` are always read-only.

To write your own, subclass `wagtail.api.v3.fields.FieldSerializer` and implement `to_representation()`. The return type hint of `to_representation()` is used as the field's type in the schema:

```python
from wagtail.api import APIField
from wagtail.api.v3.fields import FieldSerializer


class UpperCaseField(FieldSerializer):
    def to_representation(self, value) -> str:
        return value.upper()


class BlogPage(Page):
    ...

    api_fields = [
        APIField("shouting_title", serializer=UpperCaseField(source="title")),
    ]
```

The `source` argument resolves the value from another attribute, following dotted paths such as `feed_image.title`. Use `source="*"` to pass the whole object.

Serializers written for the v2 API, based on Django REST Framework fields, also work as a temporary compatibility layer, but their output may differ. See [](api_v3_migration).
