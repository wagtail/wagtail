(api_v3_permissions)=

# Permissions guide

The v3 Write API enforces Wagtail's standard permission model. This guide
explains how API-level access maps to `PermissionPolicy` classes, and provides
role-based examples.

## How permissions work

Every write operation in the v3 API calls the same permission-checking
infrastructure used by the Wagtail admin. Permission is evaluated by a
**`PermissionPolicy`** — a class that answers "can this user perform this
action on this object?"

The three core policies you will encounter:

| Policy class | Module | Used by |
|---|---|---|
| `PagePermissionPolicy` | `wagtail.permission_policies.pages` | Pages |
| `ModelPermissionPolicy` | `wagtail.permission_policies.base` | Snippets and other registered models |
| `BlanketPermissionPolicy` | `wagtail.permission_policies.base` | Always-allow / always-deny |

## Checking permissions in an endpoint

Use the policy's `.user_has_permission_for_instance()` method before any write:

```python
# api.py
from ninja import Router
from ninja.errors import HttpError
from wagtail.models import Page
from wagtail.permission_policies.pages import PagePermissionPolicy

router = Router()
page_policy = PagePermissionPolicy()


@router.post("/pages/{page_id}/publish/")
def publish_page(request, page_id: int):
    page = Page.objects.get(pk=page_id)

    # Check the user has publish permission on this specific page instance.
    if not page_policy.user_has_permission_for_instance(request.user, "publish", page):
        raise HttpError(403, "You do not have permission to publish this page.")

    revision = page.get_latest_revision()
    if revision is None:
        raise HttpError(400, "No draft revision to publish.")

    revision.publish(user=request.user)
    return {"status": "published", "page_id": page.pk}
```

## Checking snippet permissions

Snippets use `ModelPermissionPolicy`, scoped to the snippet's model class.
The following example uses bakerydemo's `BreadType` snippet:

```python
from wagtail.permission_policies.base import ModelPermissionPolicy
from breads.models import BreadType

bread_type_policy = ModelPermissionPolicy(BreadType)


@router.delete("/snippets/bread-types/{snippet_id}/")
def delete_bread_type(request, snippet_id: int):
    snippet = BreadType.objects.get(pk=snippet_id)

    if not bread_type_policy.user_has_permission_for_instance(
        request.user, "delete", snippet
    ):
        raise HttpError(403, "Permission denied.")

    snippet.delete()
    return {"status": "deleted"}
```

## Role-based permission matrix

The table below maps common Wagtail roles to what they can do via the v3 API.

| Role | Read pages | Create draft | Publish | Delete | Manage snippets |
|------|-----------|-------------|---------|--------|-----------------|
| **Anonymous** | ✅ (public pages only) | ❌ | ❌ | ❌ | ❌ |
| **Editor** | ✅ | ✅ | ❌ | ❌ | ✅ (assigned models) |
| **Moderator** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Administrator** | ✅ | ✅ | ✅ | ✅ | ✅ |

```{note}
Wagtail's permission model is **fine-grained** and per page tree. An editor
may have `publish` permission on one subtree but not another. Always check
permissions against the specific page *instance*, not just the user's group.
```

## Available permission actions

### Pages (`PagePermissionPolicy`)

| Action string | Description |
|--------|-------------|
| `add` | Create child pages under a parent |
| `edit` | Edit and save drafts |
| `publish` | Publish or unpublish |
| `bulk_delete` | Delete a page and its entire subtree |
| `lock` | Lock the page against edits |
| `unlock` | Unlock a locked page |

### Snippets / models (`ModelPermissionPolicy`)

| Action string | Description |
|--------|-------------|
| `add` | Create a new instance |
| `change` | Edit an existing instance |
| `delete` | Delete an instance |
| `view` | List / retrieve instances |

## Filtering querysets by permission

To return only objects a user is allowed to edit, use
`instances_user_has_permission_for()`:

```python
@router.get("/pages/editable/")
def list_editable_pages(request):
    """Return only pages the current user can edit."""
    qs = page_policy.instances_user_has_permission_for(request.user, "edit")
    return list(qs.values("id", "title", "slug"))
```

## Testing permissions locally (bakerydemo)

bakerydemo ships with three demo users. To test different permission levels:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `changeme` | Administrator |
| `editor` | `changeme` | Editor (no publish) |

```sh
# Get a token for the editor user (requires auth endpoint from #14298)
# Then test that publish is rejected:
curl -X POST http://localhost:8000/api/v3/pages/8/publish/ \
  -H "Authorization: Bearer <editor-token>"
# HTTP 403: {"detail": "You do not have permission to publish this page."}
```

## See also

- [](../../../topics/permissions) — Wagtail's full permission model.
- {ref}`api_v3_publishing_revisions` — publish workflow and required permissions.
- {ref}`api_v3_create_page_streamfield` — permission check for page creation.
