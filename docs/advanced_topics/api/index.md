(api)=

# Wagtail API

Wagtail provides two API options for exposing your content to external clients:

- **v3 Write API** (recommended for new projects) – a fully-featured read/write API
  built on [Django Ninja](https://django-ninja.dev/) (see {ref}`api_v3`).
- **v2 Read API** (stable, read-only) – a lightweight JSON API for reading pages,
  images, and documents (see {ref}`api_v2`).

Wagtail is built on Django, so you can also integrate other solutions such as
[GraphQL via wagtail-grapple](https://github.com/torchbox/wagtail-grapple).

---

(api_v3)=

## v3 Write API (Django Ninja)

The v3 API is the recommended approach for new projects. It supports both reads
and writes, is fully authenticated, produces audit logs, and auto-generates
OpenAPI documentation.

```{toctree}
---
maxdepth: 2
---
v3/index
```

---

(api_v2)=

## v2 Read API

The v2 API is stable and read-only. It is suitable for headless projects that
only need to read content from Wagtail.

```{toctree}
---
maxdepth: 2
---
v2/configuration
v2/usage
```
