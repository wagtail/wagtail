(api_v3_ref_snippets)=

# Snippets endpoint reference

The snippets router exposes CRUD operations for all snippet models registered
with the Wagtail snippet system.

## Base URL

```
/api/v3/snippets/{app_label}/{model_name}/
```

Example: `/api/v3/snippets/blog/author/`

## Operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v3/snippets/{app}/{model}/` | List snippet instances |
| `GET` | `/api/v3/snippets/{app}/{model}/{id}/` | Retrieve a snippet |
| `POST` | `/api/v3/snippets/{app}/{model}/` | Create a snippet |
| `PUT` | `/api/v3/snippets/{app}/{model}/{id}/` | Replace a snippet |
| `PATCH` | `/api/v3/snippets/{app}/{model}/{id}/` | Partially update a snippet |
| `DELETE` | `/api/v3/snippets/{app}/{model}/{id}/` | Delete a snippet |

## Required permissions

Permissions are evaluated by `ModelPermissionPolicy` for the specific snippet
model. See {ref}`api_v3_permissions` for details.

| Operation | Required permission |
|-----------|-------------------|
| List / retrieve | `view` |
| Create | `add` |
| Update | `change` |
| Delete | `delete` |

## Snippet models must be registered

Only models decorated with `@register_snippet` are accessible through this
router. Attempting to access an unregistered model returns `404`.

```python
# models.py
from wagtail.snippets.models import register_snippet

@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
```

## See also

- [](../../../topics/snippets/index) — registering and using snippets.
- {ref}`api_v3_permissions` — snippet permission model.
