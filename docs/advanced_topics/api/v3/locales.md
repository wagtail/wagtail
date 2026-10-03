(api_v3_locales)=

# Locales and translations

Locales are managed at `/api/v3/locales/` and are exposed for authenticated requests only, with no anonymous access. See [](api_v3_authentication) for how tokens map to permissions.

Locales are exposed as CRUD:

- `GET /locales/`: list locales.
- `GET /locales/{locale_id}/`: return one locale.
- `POST /locales/`: create a locale.
- `PUT /locales/{locale_id}/`: update a locale.
- `DELETE /locales/{locale_id}/`: delete a locale.

A locale response includes its `id`, `language_code`, `display_name`, `is_bidi` (bidirectional text), and `is_default` state. The request input is a single `language_code` value:

```sh
curl -X POST "https://example.com/api/v3/locales/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language_code": "fr"}'
```

Validation rejects duplicate or unsupported language codes, and prevents deleting the final locale or a locale that is still used by pages or other objects.

## Translation support

Beyond managing locales themselves, the v3 API supports translation workflows over the API:

- Pages support `locale` and `translation_of` [filters](api_v3_pages), and the `copy_for_translation` [page action](api_v3_pages), with optional parent, subtree, and alias behaviour.
- Snippets on a `TranslatableMixin` model support `locale` and `translation_of` [filters and a `copy_for_translation` action](api_v3_snippets).

## Locales API reference

We document the full generated OpenAPI reference for every locale endpoint from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
