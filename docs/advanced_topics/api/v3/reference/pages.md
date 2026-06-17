(api_v3_ref_pages)=

# Pages endpoint reference

The pages router exposes create, read, update, delete, and publish operations
for Wagtail pages.

## Base URL

```
/api/v3/pages/
```

## Operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v3/pages/` | List live, public pages |
| `GET` | `/api/v3/pages/{id}/` | Retrieve a single page |
| `POST` | `/api/v3/pages/` | Create a new page (draft) |
| `PUT` | `/api/v3/pages/{id}/` | Replace page content (creates revision) |
| `PATCH` | `/api/v3/pages/{id}/` | Partially update page content |
| `DELETE` | `/api/v3/pages/{id}/` | Delete a page and its children |
| `POST` | `/api/v3/pages/{id}/publish/` | Publish the latest revision |
| `POST` | `/api/v3/pages/{id}/unpublish/` | Unpublish a live page |
| `GET` | `/api/v3/pages/{id}/revisions/` | List all revisions |
| `POST` | `/api/v3/pages/{id}/revisions/{rev_id}/publish/` | Publish a specific revision |

## Common query parameters (list endpoint)

| Parameter | Type | Description |
|-----------|------|-------------|
| `child_of` | `int` | Filter by parent page id |
| `type` | `str` | Filter by page type e.g. `blog.BlogPage` |
| `slug` | `str` | Filter by slug |
| `search` | `str` | Full-text search |
| `limit` | `int` | Page size (default 20) |
| `offset` | `int` | Pagination offset |

## Required permissions

| Operation | Required permission |
|-----------|-------------------|
| List / retrieve | None (public pages) |
| Create | `add` on the parent page |
| Update | `edit` on the page |
| Publish | `publish` on the page |
| Delete | `bulk_delete` on the page |

See {ref}`api_v3_permissions` for details.

## See also

- {ref}`api_v3_create_page_streamfield` — creating pages with StreamField.
- {ref}`api_v3_publishing_revisions` — revision and publish workflows.
