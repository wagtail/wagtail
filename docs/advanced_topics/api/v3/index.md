(api_v3)=

# Wagtail API v3

Wagtail 8.0 introduces a v3 API built on [Django Ninja](https://django-ninja.dev/) and [Pydantic](https://docs.pydantic.dev/). It provides OpenAPI 3.1 schema export and declarative per-type schemas to support read and write CMS operations described in [RFC 115](https://wagtail.org/rfc-115/).

The v2 read API remains available. v3 is mounted separately at `/api/v3/`.

```{toctree}
---
maxdepth: 1
---
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

Rich text fields use the `?rich_text_format=` query parameter, which supports the same options as the project-level default of `WAGTAILAPI_RICH_TEXT_FORMAT`.

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
