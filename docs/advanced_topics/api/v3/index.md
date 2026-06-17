(api_v3)=

# Wagtail v3 Write API

The v3 API is a read/write HTTP API built on [Django Ninja](https://django-ninja.dev/)
and [Pydantic v2](https://docs.pydantic.dev/). It provides:

- Full CRUD operations on pages, images, snippets, and documents
- Token-based authentication
- Role-aware permission enforcement via Wagtail's `PermissionPolicy`
- Automatic OpenAPI / Swagger documentation at `/api/v3/docs`
- Structured audit logging for every write operation

```{toctree}
---
maxdepth: 2
---
how-to/index
permissions
reference/index
```

## Installation

Install the required dependencies:

```sh
pip install django-ninja pydantic
```

Then follow the [Django Ninja setup guide](api_ninja) to mount the API in your
project's URL configuration.

---

## Quick start: zero to published page

The following walkthrough uses [bakerydemo](https://github.com/wagtail/bakerydemo)
with its standard fixtures. After completing it you will have created a page,
saved a draft, and published it — using only API calls.

**Step 1 – Obtain a token**

Authentication is covered in {ref}`Write API: authentication guide <api_v3_auth>`
(tracked in #14298). For local testing with bakerydemo, use Django's session
auth or a personal access token.

**Step 2 – List available parent pages**

```sh
curl http://localhost:8000/api/v2/pages/?type=breads.BreadsIndexPage
# {"items": [{"id": 5, "title": "Breads", ...}]}
```

**Step 3 – Create a new BreadPage (saved as draft)**

```sh
curl -X POST http://localhost:8000/api/v3/pages/breads/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buckwheat Loaf",
    "slug": "buckwheat-loaf",
    "introduction": "A nutty, dense loaf.",
    "parent_page_id": 5,
    "body": [
      {"type": "heading", "value": "About this bread"},
      {"type": "paragraph", "value": "<p>Buckwheat gives this loaf its distinctive flavour.</p>"}
    ]
  }'
# {"id": 42, "title": "Buckwheat Loaf"}
```

**Step 4 – Save a draft revision**

```sh
curl -X POST http://localhost:8000/api/v3/pages/42/revisions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buckwheat Loaf (final)"}'
# {"revision_id": 99, "created_at": "2026-06-17T10:00:00+00:00"}
```

**Step 5 – Publish the revision**

```sh
curl -X POST http://localhost:8000/api/v3/pages/42/revisions/99/publish/ \
  -H "Authorization: Bearer <token>"
# {"status": "published", "page_id": 42}
```

**Step 6 – Verify the live page**

```sh
curl http://localhost:8000/api/v2/pages/42/?fields=title,meta
# {"id": 42, "title": "Buckwheat Loaf (final)", "meta": {"html_url": "..."}}
```

Visit the URL returned in `meta.html_url` to see the published page. You can
also view the audit log in the Wagtail admin at Settings → Audit log.

---

## How-to guides

Detailed, runnable examples for each operation type — see {ref}`how-to/index`.

## Permissions guide

How API permissions map to `PermissionPolicy`, with role-based examples — see
{ref}`api_v3_permissions`.

## API reference

Hand-written endpoint context per domain router — see `reference/index`.
