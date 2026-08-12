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

Rich text fields are stored in Wagtail's database HTML format, described in [](rich_text_internals), and the v3 API uses that format as its rich text interchange representation. Rich text fields use the `?rich_text_format=` query parameter, which supports the same options as the project-level default of `WAGTAILAPI_RICH_TEXT_FORMAT`.

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

## Documents

Documents are available at `/api/v3/documents/`. The routes are flat rather than nested under collections:

- `GET /documents/`: list documents. Anonymous access, excluding documents whose direct collection has an unpassed view restriction. Supports `?search=`, `?order=`, and field filtering.
- `GET /documents/{id}/`: document detail. Anonymous access, with the same direct-collection restriction behavior as the list endpoint.
- `POST /documents/`: create a document using `multipart/form-data`. Send the binary as `file` and writable metadata such as `title` and `collection_id` as individual form fields.
- `PATCH /documents/{id}/`: update writable metadata as JSON. The document file cannot be replaced through this endpoint.
- `DELETE /documents/{id}/`: delete a document.

The write endpoints require bearer-token authentication and the applicable Wagtail collection permissions. Wagtail's document ownership rules apply to updates and deletes: users with add permission may update or delete documents they uploaded themselves, while changing or deleting another user's document requires the corresponding permission.

Tags are returned under `meta.tags` but are not writable through the Documents API. `meta.download_url` is generated from the document's `url` property, so it uses Wagtail's configured document serving behavior. When the URL uses Wagtail's serve view, that view performs collection privacy checks before serving the file.

The API list and detail endpoints match the v2 API's direct-collection restriction behavior: a restriction on a document's direct collection can hide it, but a restriction inherited from an ancestor collection does not. The document serve view can enforce ancestor restrictions as well, so a document returned by the API is not necessarily publicly downloadable.

Document uploads enforce `WAGTAILDOCS_EXTENSIONS`, `WAGTAILDOCS_MAX_UPLOAD_SIZE`, custom form validation, and collection permissions in the same way as admin uploads. Extension validation checks the filename and does not verify that the file contents match the extension; see [](user_uploaded_files) for guidance on handling untrusted uploads.
