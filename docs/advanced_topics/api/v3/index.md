(api_v3)=

# Wagtail API v3

Wagtail 8.0 introduces a preview of a new v3 API built on [Django Ninja](https://django-ninja.dev/) and type hints. It provides OpenAPI 3.1 schema export and declarative per-type schemas to support read and write CMS operations described in [RFC 115](https://wagtail.org/rfc-115/).

```{toctree}
---
maxdepth: 1
---
authentication
pages
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

Then register the API URLs in your project. While v3 is in preview, we recommend mounting it at `/api/v3-preview/` to signify that it may change as part of an upcoming release:

```python
# urls.py
from wagtail.api.v3.urls import api

urlpatterns = [
    path("api/v3-preview/", api.urls),
    # You can also mount it at /api/v3/ if you prefer:
    # path("api/v3/", api.urls),
]
```

This will expose all endpoints at the API root you decided. This includes read-only endpoints, write-only endpoints (protected with authentication and permission checks). Which endpoints are available depends on which Wagtail apps are in `INSTALLED_APPS` on your project. Pages are always available, while images, documents, snippets, locales, and redirects appear only when their app is installed and their models are registered.

To get started, browse the generated docs:

- A human-friendly documentation dashboard at `<API root>/docs/`
- A machine-readable OpenAPI schema at `<API root>/openapi.json`

The OpenAPI schema (`<API root>/openapi.json`) and the interactive docs dashboard (`<API root>/docs/`) are publicly available, including descriptions of both anonymous and authenticated endpoints. To add a layer of obscurity, you can set the [`WAGTAILAPI_DOCS_ENABLED`](wagtailapi_settings) setting to `False` to disable both routes.

The v3 API reads the same `WAGTAILAPI_*` settings as v2 where applicable (`WAGTAILAPI_BASE_URL`, `WAGTAILAPI_LIMIT_MAX`, `WAGTAILAPI_SEARCH_ENABLED`, `WAGTAILAPI_RICH_TEXT_FORMAT`). See [](api_v2_configuration) and the [API settings reference](wagtailapi_settings).

## What's included

The v3 API supports a wide range of CMS operations, largely covering the same functionality as the Wagtail admin interface. This includes:

- Pages, including drafts, revisions, and page actions.
- Sites, locales, and redirects.
- Images and documents.
- API-enabled snippets.
- Rich text in HTML and Markdown.
- StreamField content.
- Schema discovery and the OpenAPI reference.

This covers a wide range of Wagtail capabilities but not all of it. [Share your feedback](https://github.com/wagtail/wagtail/discussions/14531) on what you would like to see next, including:

- Workflow / moderation operations (for example submitting, approving, or rejecting).
- Support for Site settings.
- Precise StreamField block schemas.
- Official client libraries or UIs that reuse the API.
- Deprecation and eventual removal of the v2 API.
- Official API tutorial.

## Pagination

List endpoints use limit/offset pagination, with a `count` in responses that is the total number of results irrespective of pagination:

```json
{
    "count": 42,
    "items": []
}
```

Use `?limit` and `?offset` query parameters to page through results. `WAGTAILAPI_LIMIT_MAX` caps the maximum `limit` value (see the [API settings reference](wagtailapi_settings)).

## Error handling

Handled API errors use `application/problem+json` from [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807). This covers validation failures at the schema, content, and model layers (HTTP 422), permission failures (`401` unauthenticated, `403` authenticated), `404`, and explicit framework errors. Here’s an example of a validation failure:

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
Unhandled exceptions are not converted to this envelope: in production (`DEBUG=False`) they are re-raised for Django's own handling, so they may not use `application/problem+json`.
```
