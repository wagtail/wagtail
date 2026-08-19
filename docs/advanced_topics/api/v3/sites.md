(api_v3_sites)=

# Sites

Sites are managed at `/api/v3/sites/` and are exposed for authenticated requests only, with no anonymous access. See [](api_v3_authentication) for how tokens map to permissions.

Sites are exposed as CRUD:

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

The full, generated OpenAPI reference for every site endpoint — request and response shapes included — is rendered from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
