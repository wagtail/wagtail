(api_v3)=

# Wagtail API v3

Wagtail 8.0 introduces a preview of the v3 API, which can read and write CMS content as described in [RFC 115](https://wagtail.org/rfc-115/). It's built on [Django Ninja](https://django-ninja.dev/) and provides an OpenAPI 3.1 schema.

```{toctree}
---
maxdepth: 1
---
authentication
pages
workflows
images
documents
snippets
redirects
streamfield
rich_text
sites
locales
schema
reference
migration
```

## Quick start

First, add `wagtail.api.v3` to `INSTALLED_APPS` in your Django project settings:

```python
# settings.py

INSTALLED_APPS = [
    ...

    'wagtail.api.v3',

    ...
]
```

Then register the API URLs in your project. While v3 is in preview, we recommend mounting it at `/api/v3-preview/` to signify that it may change in an upcoming release:

```python
# urls.py
from django.urls import path
from wagtail.api.v3.urls import api

urlpatterns = [
    path("api/v3-preview/", api.urls),
    # You can also mount it at /api/v3/ if you prefer:
    # path("api/v3/", api.urls),
]
```

The above example will mount the API root at `/api/v3-preview/`. This includes read-only endpoints and write endpoints (protected with authentication and permission checks).

Available endpoints depend on which Wagtail apps are in `INSTALLED_APPS`. Pages are always available, while images, documents, snippets, locales, and redirects appear only when their app is installed.

To get started, browse the generated docs:

- `<API root>/docs/`: a human-friendly documentation dashboard
- `<API root>/openapi.json`: a machine-readable OpenAPI schema

Both are public and describe anonymous and authenticated endpoints. To disable them, set [`WAGTAILAPI_DOCS_ENABLED`](wagtailapi_settings) to `False`.

The v3 API reads the same `WAGTAILAPI_*` settings as v2 where applicable (`WAGTAILAPI_BASE_URL`, `WAGTAILAPI_LIMIT_MAX`, `WAGTAILAPI_SEARCH_ENABLED`, `WAGTAILAPI_RICH_TEXT_FORMAT`). See [](api_v2_configuration) and the [API settings reference](wagtailapi_settings).

## What's included

The v3 API includes support for:

- Pages, including drafts, revisions, and page actions.
- Workflow / moderation operations for pages and snippets.
- Sites, locales, and redirects.
- Images and documents.
- API-enabled snippets.
- Rich text in HTML and Markdown.
- StreamField content.
- Schema discovery and the OpenAPI reference.

This covers a wide range of CMS operations that are available in the Wagtail admin interface, but not all of them. [Share your feedback](https://github.com/wagtail/wagtail/discussions/14531) on what you would like to see next, including:

- Support for Site settings.
- Precise StreamField block schemas.
- Official client libraries or UIs that reuse the API.
- Official API tutorial.

The v3 API replaces the v2 API, which is planned for deprecation in a future release. See the [deprecation timeline](api_v2_deprecation) and [](api_v3_migration).

(api_v3_pagination)=

## Pagination

List endpoints use `?limit` and `?offset` query parameters for pagination. The `count` in responses is the total number of results without pagination:

```json
{
    "count": 42,
    "items": []
}
```

`WAGTAILAPI_LIMIT_MAX` caps the maximum `limit` value (see the [API settings reference](wagtailapi_settings)).

## Error handling

Handled API errors use `application/problem+json` from [RFC 9457](https://datatracker.ietf.org/doc/html/rfc9457) with the following status codes:

- `400`: malformed request
- `401`: the endpoint needs authentication and no valid token was sent
- `403`: the user does not have permission
- `404`: not found
- `422`: validation failed (at any of the schema, content, and model layers), with details in errors

```json
{
    "type": "about:blank",
    "title": "Unprocessable Entity",
    "status": 422,
    "detail": "Validation failed",
    "errors": [
        {
            "type": "invalid",
            "loc": ["slug"],
            "msg": "The slug 'blog' is already in use within the parent page."
        }
    ]
}
```

```{note}
Unhandled exceptions do not use this format: in production (`DEBUG=False`) they are re-raised to be handled by Django's standard error handling.
```
