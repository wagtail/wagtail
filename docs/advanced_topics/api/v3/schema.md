(api_v3_schema)=

# Schema discovery

The v3 API exposes its generated JSON schemas so clients can discover what each content type accepts and returns, without hand-copying field definitions. Schema discovery requires an authenticated request.

## Listing registered content types

The `/schema/` endpoint lists the content types registered with the API. Each entry has a `name` (the exact Django model label, or the generic `pages`) and a `label` (a human-readable name):

```sh
curl -H "Authorization: Bearer $TOKEN" "https://example.com/api/v3/schema/"
```

```json
{
    "types": [
        {"name": "pages", "label": "Pages"},
        {"name": "tests.BlogPage", "label": "Blog page"},
        {"name": "mymodels.Advert", "label": "Advert"}
    ]
}
```

The registered types depend on the project's installed apps and registered models, so the exact list is specific to each site.

## Reading the schemas for a content type

The `/schema/{type_name}/` endpoint returns the JSON schemas for a single content type, split by direction: `read`, `create`, and `patch`:

- The `read` schema describes what the API returns for that type.
- The `create` schema describes what you can submit to create an instance.
- The `patch` schema describes what you can submit to update an instance.

```sh
curl -H "Authorization: Bearer $TOKEN" \
  "https://example.com/api/v3/schema/tests.BlogPage/"
```

An unknown content type returns `404`.

## How schemas are generated

Schemas are generated at runtime from the project's models and panels, not hand-written. The read side comes from a model's `api_fields`, and the write side additionally requires a field to be a real editable model field declared `APIField(..., writable=True)`. A field that is readable but not exposed as writable appears in `read` but not in `create` or `patch`.

### Exposing writable fields

To allow a field to be submitted when creating or updating content through the API, declare it with `writable=True`:

```python
# blog/models.py

from wagtail.api import APIField
from wagtail.models import Page


class BlogPage(Page):
    body = RichTextField()
    feed_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL
    )
    internal_notes = models.TextField(blank=True)

    api_fields = [
        APIField("body", writable=True),
        APIField("feed_image", writable=True),
        APIField("internal_notes"),  # readable only — in read schema, not create/patch
    ]
```

Fields without `writable=True` still appear in API read responses and the `read` schema, but are omitted from the `create` and `patch` schemas. Only real model fields can be writable: computed properties and custom `serializer` fields that do not map to an editable model field cannot be marked writable.

For inline child relations (`InlinePanel` / `ParentalKey`), mark the relation writable and declare the child model's fields as writable too:

```python
from modelcluster.fields import ParentalKey
from wagtail.models import Orderable


class BlogPageCarouselItem(Orderable):
    page = ParentalKey("blog.BlogPage", related_name="carousel_items")
    caption = models.CharField(max_length=255)

    api_fields = [
        APIField("caption", writable=True),
    ]


class BlogPage(Page):
    # ...

    api_fields = [
        APIField("body", writable=True),
        APIField("carousel_items", writable=True),
    ]
```

Because the generic `pages` entry is for discovery across all page types, only its `read` schema is populated today: its `create` and `patch` directions fall back to a `Not yet available` placeholder. Use a concrete page type registration (for example `tests.BlogPage`) to get actionable `create` and `patch` schemas.

## Compared with the v2 API

The v2 API exposes fields through a dynamic `?fields=` query projection. The v3 API instead uses these fixed generated schemas and does not support `?fields=` projection. The [v2 to v3 migration guide](api_v3_migration) describes the practical differences in detail.
