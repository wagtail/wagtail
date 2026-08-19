(api_v3_sites_locales_redirects)=

# Sites, locales, and redirects

Alongside [pages](api_v3_pages), [media](api_v3_images), and [snippets](api_v3_snippets), the v3 API exposes three more management domains: sites, locales, and redirects. Sites and locales are bearer-only; redirects allow anonymous reads because they represent public routing behaviour.

```{note}
Sites and locales are managed exclusively with an authenticated request. Redirect reads are public, but redirect writes still require a token. See [](api_v3_authentication) for how tokens map to permissions.
```

## Sites

Sites are managed at `/api/v3/sites/` as bearer-only CRUD:

- `GET /sites/` — list sites.
- `GET /sites/{site_id}/` — return one site.
- `POST /sites/` — create a site.
- `PUT /sites/{site_id}/` — update a site.
- `DELETE /sites/{site_id}/` — delete a site.

A site is described by its `id`, `hostname`, `port`, `site_name`, `root_page_id`, and `is_default_site` state. The list and detail endpoints are filtered by the permission policy, so a caller only sees sites they have a permission on.

Create and update take the site fields as JSON and go through `SiteForm`, so the same rules apply as in the admin: hostname normalization, uniqueness and default-site constraints, root page validation, and cache invalidation. Mutations run through Wagtail actions and return `201` on create and `204` on delete. Creating a site:

```sh
curl -X POST "https://example.com/api/v3/sites/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname": "www.example.com", "port": 443, "site_name": "Example", "root_page_id": 4, "is_default_site": true}'
```

## Locales and translations

Locales are managed at `/api/v3/locales/` as bearer-only CRUD:

- `GET /locales/` — list locales.
- `GET /locales/{locale_id}/` — return one locale.
- `POST /locales/` — create a locale.
- `PUT /locales/{locale_id}/` — update a locale.
- `DELETE /locales/{locale_id}/` — delete a locale.

A locale response includes its `id`, `language_code`, `display_name`, `is_bidi` (bidirectional text), and `is_default` state. The request input is a single `language_code` value:

```sh
curl -X POST "https://example.com/api/v3/locales/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language_code": "fr"}'
```

Validation rejects duplicate or unsupported language codes, and prevents deleting the final locale or a locale that is still used by pages or other objects.

### Translation support

Beyond managing locales themselves, the v3 API supports translation workflows over the API:

- Pages support `locale` and `translation_of` [filters](api_v3_pages), and the `copy_for_translation` [page action](api_v3_pages), with optional parent, subtree, and alias behaviour.
- Snippets on a `TranslatableMixin` model support `locale` and `translation_of` [filters and a `copy_for_translation` action](api_v3_snippets).

```{note}
`copy_for_translation` creates the initial translated copy. There is no API for ongoing synchronization of translations or for `wagtail-localize` workflows; those remain outside the v3 API in this release.
```

## Redirects

Redirects are managed at `/api/v3/redirects/`:

- `GET /redirects/` — list redirects. Public for anonymous read.
- `GET /redirects/find/` — resolve a redirect and redirect to its canonical detail. Public for anonymous read.
- `GET /redirects/{redirect_id}/` — return one redirect. Public for anonymous read.
- `POST /redirects/` — create a redirect. Requires a token.
- `PUT /redirects/{redirect_id}/` — update a redirect. Requires a token.
- `DELETE /redirects/{redirect_id}/` — delete a redirect. Requires a token.

Redirect reads are public because the redirect middleware resolves redirects publicly; the endpoints behave like the v2 API in this regard.

A redirect is described by its `id`, `old_path`, nullable `site_id`, `is_permanent`, `redirect_page_id`, `redirect_page_route_path`, `redirect_link`, `automatically_created`, and `created_at`. The list supports exact filtering and ordering but not search.

The `find` endpoint resolves `html_path` through Wagtail's redirect middleware, or falls back to matching by `id`, then responds with a `302` redirect to the canonical detail:

```sh
curl "https://example.com/api/v3/redirects/find/?html_path=/old-page/"
```

```{note}
As with page `find`, the OpenAPI schema describes `find` as returning the redirect detail schema, but the runtime response is a `302` redirect. Clients generated from OpenAPI should follow the redirect to the detail URL.
```

Creates and updates go through `RedirectForm`, which provides path normalization and duplicate validation. Redirects are not swappable, and redirect CRUD instantiates the generic action classes directly, so project action-registry overrides do not affect redirect mutations.

### Example: create a redirect and resolve it

This example redirects an old missing URL to an existing page, then resolves the old path. It assumes a `BASE` pointing at the mounted API, a bearer `TOKEN`, and an existing page with ID `9`.

Create the redirect with the old path and the destination page:

```sh
curl -X POST "$BASE/redirects/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_path": "/old-location/", "redirect_page_id": 9, "is_permanent": true}'
```

Resolve the old path. The endpoint follows the redirect and returns the canonical redirect detail:

```sh
curl "$BASE/redirects/find/?html_path=/old-location/"
```

The full, generated OpenAPI reference for every site, locale, and redirect endpoint — request and response shapes included — is rendered from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
