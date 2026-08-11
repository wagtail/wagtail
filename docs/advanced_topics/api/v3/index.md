(api_v3)=

# Wagtail API v3

Wagtail 8.0 introduces a v3 API built on [Django Ninja](https://django-ninja.dev/) and [Pydantic](https://docs.pydantic.dev/). It provides OpenAPI 3.1 schema export and declarative per-type schemas to support read and write CMS operations described in [RFC 115](https://wagtail.org/rfc-115/).

The v2 read API remains available. v3 is mounted separately at `/api/v3/`.

```{toctree}
---
maxdepth: 1
---
authentication
reference
```

## Quick start

Register the API URLs in your project:

```python
# urls.py
from wagtail.api.v3.urls import api

urlpatterns = [
    path("api/v3/", api.urls),
]
```

Browse the interactive docs at `/api/v3/docs` and the OpenAPI schema at `/api/v3/openapi.json`.

The v3 API reads the same `WAGTAILAPI_*` settings as v2 where applicable (`WAGTAILAPI_BASE_URL`, `WAGTAILAPI_LIMIT_MAX`, `WAGTAILAPI_SEARCH_ENABLED`, `WAGTAILAPI_RICH_TEXT_FORMAT`). See [](api_v2_configuration) and the [API settings reference](wagtailapi_settings).

## Pagination

List endpoints use Django Ninja's limit/offset pagination:

```json
{
    "count": 42,
    "items": []
}
```

`count` is the total number of results irrespective of pagination. Use `?limit` and `?offset` query parameters to page through results. `WAGTAILAPI_LIMIT_MAX` caps the maximum `limit` value (see [](api_v2_configuration) and the [API settings reference](wagtailapi_settings)).

## Rich text

Rich text fields are stored in Wagtail's database HTML format, described in [](rich_text_internals), and the v3 API uses that format as its rich text interchange representation.

### Writing rich text

On write endpoints, a rich text field accepts either a plain string, interpreted as database HTML:

```json
{
    "body": "<p>Hello <a linktype=\"page\" id=\"3\">world</a></p>"
}
```

or an envelope with an explicit format:

```json
{
    "body": {"format": "db_html", "content": "<p>Hello world</p>"}
}
```

`db_html` is the only supported input format, and is the default when `format` is omitted.
Anything else is rejected with a 422 validation error.

All input is sanitised against the field's declared `features`, including plain strings.
Constructs outside the feature set are removed rather than rejected, and every removal is itemised in `meta.warnings` on create and update responses:

```json
{
    "meta": {
        "type": "blog.BlogPage",
        "warnings": [
            {
                "field": "body",
                "tag": "h1",
                "action": "unwrapped",
                "reason": "feature_disabled",
                "detail": "<h1>Title</h1>"
            }
        ]
    }
}
```

`action` is `"unwrapped"` when the element was removed but its text content kept, or `"removed"` when the element and its content were removed.
`reason` is one of `"feature_disabled"` (the element isn't in the field's feature set), `"unknown_linktype"`, `"unknown_embedtype"`, or `"missing_attribute"` (an internal reference missing its required attribute, such as `<a linktype="page">` without an `id`).
`detail` is a short snippet of the affected source markup — it is raw input content, and clients must treat it as untrusted.
`meta.warnings` is `null` when nothing was stripped.

Internal references must use the database HTML idioms: `<a linktype="page" id="3">`, `<a linktype="document" id="5">`, `<embed embedtype="image" id="42" alt="..." format="left"/>`, `<embed embedtype="media" url="..."/>`.
External links are plain `<a href="https://...">`.
The API does not resolve `href` or `src` URLs back to CMS objects, and unknown link or embed types are stripped.
References to missing pages, images, or documents are preserved as-is, matching how the rich text editor handles broken references.

On create, omitting a rich text field stores the field's empty representation rather than failing validation, even for required fields — matching what the admin editor submits for an untouched field.
(On update, unmentioned fields are left unchanged, as with any other field.)

### Reading rich text

On the page detail endpoint and on create/update responses, use the `?rich_text_format=` query parameter to choose the output format: `db_html` (the default) returns the database HTML as stored, while `html` returns display-ready HTML with internal references expanded, equivalent to the `|richtext` template filter.
An invalid value returns a 400 error.
The project-wide default can be changed with the `WAGTAILAPI_RICH_TEXT_FORMAT` setting — see the v2 documentation section on [rich text in the API](api_v2_configuration) and the [API settings reference](wagtailapi_settings).
List endpoints do not include rich text fields, so they do not accept `rich_text_format`.

Schema responses (and the OpenAPI document) list each rich text field's allowed `features`, so clients can adapt their input up front instead of relying on `meta.warnings` after the fact.

## Error format

All error responses use [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) `application/problem+json`:

```json
{
    "type": "https://docs.wagtail.org/api/v3/validation-error",
    "title": "Unprocessable Entity",
    "status": 422,
    "detail": "Validation failed",
    "errors": []
}
```

## Images

Images are available at `/api/v3/images/`:

- `GET /images/`: list images. Anonymous access, excluding images in restricted collections. Supports `?search=`, `?order=`, and filtering on the image's own fields (`title`, `width`, `height`, plus any `api_fields` the project declares) via query parameters.
- `GET /images/{id}/`: image detail.
- `POST /images/`: create an image. This endpoint uses `multipart/form-data`: the `file` field carries the image binary, and writable metadata (title, description, collection, focal point) is sent as individual form fields.
- `PATCH /images/{id}/`: update the same writable metadata as JSON. Does not support changing the image file itself.

Tags are returned in image responses under `meta.tags`, but are not writable through the images API yet.
- `DELETE /images/{id}/`: delete an image.

Image writes enforce the same validation (max upload size, max pixels, extensions) and collection permissions as the admin.

### Image renditions

Renditions are exposed per-project through `api_fields`, the same mechanism as [in the v2 API](api_v2_images):

```python
from wagtail.images.api.fields import ImageRenditionField


class BlogPage(Page):
    ...

    api_fields = [
        APIField("thumbnail", serializer=ImageRenditionField("fill-300x300")),
    ]
```
