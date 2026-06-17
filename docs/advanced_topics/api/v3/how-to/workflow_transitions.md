(api_v3_workflow_transitions)=

# How to trigger workflow transitions

Wagtail's moderation workflows can be driven via the v3 API. This guide shows
how to submit a page for moderation and approve or reject a workflow task.

## Prerequisites

- Wagtail v3 Write API installed and mounted (see {ref}`api_ninja`).
- A workflow is configured in the Wagtail admin and assigned to the target page
  type (Settings → Workflows).
- The authenticated user has appropriate workflow permissions.

## Submitting a page for moderation

Save a revision first, then submit it to the workflow assigned to that page:

```python
# api.py
from ninja import Router
from ninja.errors import HttpError
from wagtail.models import Page, WorkflowState

router = Router()


@router.post("/pages/{page_id}/submit-for-moderation/")
def submit_for_moderation(request, page_id: int):
    """Submit the latest draft revision to the page's assigned workflow."""
    page = Page.objects.get(pk=page_id).specific
    revision = page.get_latest_revision()

    if revision is None:
        raise HttpError(400, "No revision to submit. Save a draft first.")

    workflow = page.get_workflow()
    if workflow is None:
        raise HttpError(400, "No workflow is assigned to this page type.")

    # workflow.start() creates a WorkflowState and assigns the first task.
    workflow.start(page, request.user)

    state = WorkflowState.objects.filter(page_id=page_id).order_by("-created_at").first()
    return {
        "workflow": workflow.name,
        "current_task": state.current_task_state.task.name,
        "status": state.status,
    }
```

## Checking workflow state

```python
@router.get("/pages/{page_id}/workflow-state/")
def get_workflow_state(request, page_id: int):
    """Return the current workflow state for a page."""
    state = (
        WorkflowState.objects
        .filter(page_id=page_id)
        .order_by("-created_at")
        .first()
    )
    if state is None:
        return {"status": "no_active_workflow"}

    return {
        "workflow": state.workflow.name,
        "status": state.status,
        "current_task": (
            state.current_task_state.task.name
            if state.current_task_state
            else None
        ),
    }
```

## Approving a task

Use `task.on_action()` to approve a task state. This is the correct public API —
it applies the action, advances the workflow, and records the audit log entry:

```python
from wagtail.models import TaskState


@router.post("/workflow-tasks/{task_state_id}/approve/")
def approve_task(request, task_state_id: int):
    """Approve the given workflow task, advancing the workflow."""
    task_state = TaskState.objects.get(pk=task_state_id)

    # on_action is defined on the Task model; task.specific resolves subclass.
    task_state.task.specific.on_action(
        task_state=task_state,
        user=request.user,
        action_name="approve",
    )
    return {"status": "approved"}
```

## Rejecting a task

```python
@router.post("/workflow-tasks/{task_state_id}/reject/")
def reject_task(request, task_state_id: int, comment: str = ""):
    """Reject the workflow task with an optional comment."""
    task_state = TaskState.objects.get(pk=task_state_id)
    task_state.task.specific.on_action(
        task_state=task_state,
        user=request.user,
        action_name="reject",
        comment=comment,
    )
    return {"status": "rejected"}
```

## Full moderation flow example

```sh
# 1. Save a draft first (see publishing_revisions guide)
curl -X POST http://localhost:8000/api/v3/pages/8/revisions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Sourdough (updated for review)"}'
# {"revision_id": 12, "created_at": "..."}

# 2. Submit for moderation
curl -X POST http://localhost:8000/api/v3/pages/8/submit-for-moderation/ \
  -H "Authorization: Bearer <token>"
# {"workflow": "Default Workflow", "current_task": "Moderators approval", "status": "in_progress"}

# 3. Check state
curl http://localhost:8000/api/v3/pages/8/workflow-state/ \
  -H "Authorization: Bearer <token>"
# {"workflow": "Default Workflow", "status": "in_progress", "current_task": "Moderators approval"}

# 4. Approve task id 7 (as a moderator user)
curl -X POST http://localhost:8000/api/v3/workflow-tasks/7/approve/ \
  -H "Authorization: Bearer <moderator-token>"
# {"status": "approved"}
```

```{note}
When all tasks in a workflow are approved, Wagtail automatically publishes
the page if the workflow's final action is set to "Publish". Check your
workflow configuration in Settings → Workflows.
```

## See also

- {ref}`api_v3_publishing_revisions` — publishing and reverting revisions directly.
- [](../../../topics/snippets/index) — workflow support for snippets.
