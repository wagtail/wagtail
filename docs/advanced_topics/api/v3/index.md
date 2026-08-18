(api_v3)=

# Wagtail API v3

Wagtail 8.0 introduces a preview of a new v3 API built on [Django Ninja](https://django-ninja.dev/) and type hints. It provides OpenAPI 3.1 schema export and declarative per-type schemas to support read and write CMS operations described in [RFC 115](https://wagtail.org/rfc-115/).

```{toctree}
---
maxdepth: 1
---
authentication
documents
images
migration
pages
permissions
python_api
reference
rich_text
schema
sites_locales_redirects
snippets
streamfield
```

## Quick start

Register the API URLs in your project. While v3 is in preview, we recommend mounting it at `/api/v3-preview/` to signify that it may change as part of an upcoming release:

```python
# urls.py
from wagtail.api.v3.urls import api

urlpatterns = [
    path("api/v3-preview/", api.urls),
    # You can also mount it at /api/v3/ if you prefer:
    # path("api/v3/", api.urls),
]
```

Browse the interactive docs at `/api/v3/docs` and the OpenAPI schema at `/api/v3/openapi.json`.

The v3 API reads the same `WAGTAILAPI_*` settings as v2 where applicable (`WAGTAILAPI_BASE_URL`, `WAGTAILAPI_LIMIT_MAX`, `WAGTAILAPI_SEARCH_ENABLED`, `WAGTAILAPI_RICH_TEXT_FORMAT`). See [](api_v2_configuration) and the [API settings reference](wagtailapi_settings).

```{warning}
Mounting the v3 API enables write operations on your content. The available surface depends on which Wagtail apps are in `INSTALLED_APPS` and which content models are registered — pages are always available, while images, documents, snippets, locales, and redirects appear only when their app is installed and their models are registered. Only a selection of endpoints allow anonymous access; write operations require an authenticated bearer token. See [](api_v3_authentication) for tokens and permissions.
```

## What's included and what's not

The v3 API supports read and write CMS operations across:

- pages, including drafts, revisions, and page actions;
- sites, locales, and redirects;
- images and documents;
- API-enabled snippets;
- rich text and Markdown, with `wagtail://` references;
- StreamField content;
- schema discovery and the OpenAPI reference;
- bearer-token authentication.

The following are not available through v3 in this release:

- workflow and moderation operations (for example submitting, approving, or rejecting);
- an official API client CLI — a server-side `api_tokens` management command is available instead;
- deprecation or removal of the v2 API — the v2 read API remains available and unchanged.

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

### Input formats

On writes, a top-level page rich text field value accepts either a plain string (database HTML, sanitised against the field's declared features) or an envelope object:

```json
"body": {"format": "db_markdown", "content": "# Title\n\n[about](wagtail://page?id=3)"}
```

Supported input formats:

- `db_html`: database HTML (the default when `format` is omitted).
- `db_markdown`: Markdown using the `wagtail://` reference syntax described below.

Markdown input is converted and sanitized for storage as database HTML.

```{note}
These string and envelope input formats are guaranteed for top-level page rich text fields. Rich text fields on other models (for example snippets) do not currently share the same input conversion path, so treat string and envelope input there as unsupported.
```

Sanitization removes content that is not allowed by the field's features, and these removals are not reported back to the caller: a response can silently contain less than what was submitted.

### Output formats

Rich text fields use the `?rich_text_format=` query parameter, which supports the same options as the project-level default of [`WAGTAILAPI_RICH_TEXT_FORMAT`](wagtailapi_settings):

- `db_html` (default): Wagtail's [internal storage format](rich_text_internals).
- `html`: display-ready HTML, converted like in templates.
- `db_markdown`: Markdown that preserves internal references as `wagtail://` URLs, similarly to `db_html`.
- `markdown`: Markdown with references resolved to public URLs (page URLs, image rendition URLs), like `html`.

## Error format

Handled API errors use [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) `application/problem+json`. This covers validation failures at the schema, content (block/rich-text), and model layers (HTTP 422), permission failures (`401` unauthenticated, `403` authenticated), `404`, and explicit framework errors. Rich text format errors are returned as HTTP 400:

```json
{
    "type": "about:blank",
    "title": "Unprocessable Entity",
    "status": 422,
    "detail": "Validation failed",
    "errors": []
}
```

```{note}
Otherwise-unhandled exceptions are not converted to this envelope: in production (`DEBUG=False`) they are re-raised for Django's own handling, so they may not use `application/problem+json`.
```

```{note}
An unrecognized `rich_text_format` value is rejected with HTTP 422 on top-level typed fields, but returns HTTP 400 when the value appears inside an untyped StreamField block.
```

## Images

Images are available at `/api/v3/images/`: anonymous list and detail reads, and bearer-token upload, metadata update, and delete, with the same validation and collection permissions as the admin. See [](api_v3_images) for the full reference, including custom image models and renditions.

## Documents

Documents are available at `/api/v3/documents/`: anonymous list and detail reads, and bearer-token upload, metadata update, and delete, with the same validation and collection permissions as the admin. See [](api_v3_documents) for the full reference, including custom document models.
