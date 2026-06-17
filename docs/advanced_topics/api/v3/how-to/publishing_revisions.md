(api_v3_publishing_revisions)=

# How to publish, create revisions, and revert pages

This guide covers scripted publishing workflows: saving draft revisions,
publishing a page, and reverting to a previous revision using Wagtail's
action classes.

## Prerequisites

- Wagtail v3 Write API installed and mounted (see {ref}`api_ninja`).
- The authenticated user has `edit` permission to save drafts and `publish`
  permission to make content live.

## Creating a draft revision

A **revision** is a point-in-time snapshot of a page's content. Saving a
revision does not make content live — it creates a draft. Use
`page.save_revision()`:

```python
# api.py
from ninja import Router, Schema
from ninja.errors import HttpError
from wagtail.models import Page, Revision
from wagtail.permission_policies.pages import PagePermissionPolicy

router = Router()
page_policy = PagePermissionPolicy()


class PageUpdateIn(Schema):
    title: str
    introduction: str | None = None


@router.post("/pages/{page_id}/revisions/")
def create_revision(request, page_id: int, payload: PageUpdateIn):
    """Save a new draft revision without publishing."""
    page = Page.objects.get(pk=page_id).specific

    if not page_policy.user_has_permission_for_instance(request.user, "edit", page):
        raise HttpError(403, "You do not have permission to edit this page.")

    page.title = payload.title
    # Only update `introduction` if the page type has it (e.g. BreadPage).
    if payload.introduction is not None and hasattr(page, "introduction"):
        page.introduction = payload.introduction

    revision = page.save_revision(user=request.user)
    return {
        "revision_id": revision.pk,
        "created_at": revision.created_at.isoformat(),
    }
```

## Publishing a revision

Call `revision.publish()` to make a revision live. Wagtail writes an audit log
entry and fires the `page_published` signal automatically:

```python
@router.post("/pages/{page_id}/revisions/{revision_id}/publish/")
def publish_revision(request, page_id: int, revision_id: int):
    """Publish a specific draft revision."""
    revision = Revision.page_revisions.get(pk=revision_id, object_id=page_id)
    page = revision.as_object()

    if not page_policy.user_has_permission_for_instance(request.user, "publish", page):
        raise HttpError(403, "You do not have permission to publish this page.")

    revision.publish(user=request.user)
    return {"status": "published", "page_id": page_id}
```

To always publish the most recent draft, use:

```python
latest = Page.objects.get(pk=page_id).get_latest_revision()
latest.publish(user=request.user)
```

## Listing revisions

```python
@router.get("/pages/{page_id}/revisions/")
def list_revisions(request, page_id: int):
    """Return all revisions for a page, newest first."""
    revisions = (
        Revision.page_revisions
        .filter(object_id=page_id)
        .order_by("-created_at")
        .values("id", "created_at")
    )
    return list(revisions)
```

## Reverting to a previous revision

Use `RevertToPageRevisionAction` to revert — this is the correct Wagtail action
class for reversals. It saves a *new* revision containing the old content and
then publishes it, preserving full history:

```python
from wagtail.actions.revert_to_page_revision import RevertToPageRevisionAction


@router.post("/pages/{page_id}/revisions/{revision_id}/revert/")
def revert_to_revision(request, page_id: int, revision_id: int):
    """Revert the live page to the content stored in an older revision."""
    revision = Revision.page_revisions.get(pk=revision_id, object_id=page_id)
    page = Page.objects.get(pk=page_id)

    if not page_policy.user_has_permission_for_instance(request.user, "publish", page):
        raise HttpError(403, "You do not have permission to revert this page.")

    action = RevertToPageRevisionAction(page=page, revision=revision, user=request.user)
    new_revision = action.execute()
    new_revision.publish(user=request.user)

    return {
        "status": "reverted_and_published",
        "page_id": page_id,
        "reverted_to_revision_id": revision_id,
    }
```

```{note}
`RevertToPageRevisionAction.execute()` saves a **new** revision containing the
old content. The original revision history is never deleted. You can inspect
the full history with the list revisions endpoint above.
```

## Full publish-from-scratch example (bakerydemo)

The following sequence creates a draft, then publishes it for a BreadPage
(pk=8 in the standard bakerydemo fixtures):

```sh
# 1. Save a draft revision
curl -X POST http://localhost:8000/api/v3/pages/8/revisions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Whole Wheat Sourdough (updated)"}'
# {"revision_id": 12, "created_at": "2026-06-17T10:00:00+00:00"}

# 2. Publish that revision
curl -X POST http://localhost:8000/api/v3/pages/8/revisions/12/publish/ \
  -H "Authorization: Bearer <token>"
# {"status": "published", "page_id": 8}

# 3. Verify via the v2 read API
curl http://localhost:8000/api/v2/pages/8/?fields=title
# {"id": 8, "title": "Whole Wheat Sourdough (updated)", ...}
```

## See also

- {ref}`api_v3_workflow_transitions` — submitting pages for moderation before publishing.
- {ref}`api_v3_permissions` — permission model and `PagePermissionPolicy`.
- [](../../../reference/pages/index) — Wagtail page model reference.
