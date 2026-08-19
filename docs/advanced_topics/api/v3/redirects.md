(api_v3_redirects)=

# Redirects

Redirects are managed at `/api/v3/redirects/`. Reads are public for anonymous requests; writes require an authenticated request. See [](api_v3_authentication) for how tokens map to permissions.

Redirects are exposed as CRUD:

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

## Example: create a redirect and resolve it

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

The full, generated OpenAPI reference for every redirect endpoint — request and response shapes included — is rendered from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
