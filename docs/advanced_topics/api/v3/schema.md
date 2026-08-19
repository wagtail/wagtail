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

Because the generic `pages` entry is for discovery across all page types, only its `read` schema is populated today: its `create` and `patch` directions fall back to a `Not yet available` placeholder. Use a concrete page type registration (for example `tests.BlogPage`) to get actionable `create` and `patch` schemas.

## Compared with the v2 API

The v2 API exposes fields through a dynamic `?fields=` query projection. The v3 API instead uses these fixed generated schemas and does not support `?fields=` projection. The [v2 to v3 migration guide](api_v3_migration) describes the practical differences in detail.
