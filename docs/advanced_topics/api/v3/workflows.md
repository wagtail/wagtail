(api_v3_workflows)=

# Workflows

Moderation workflows are exposed for pages and for snippet models using {class}`~wagtail.models.WorkflowMixin`. You can submit an object for moderation, approve or reject the current moderation task, resume a workflow after changes were requested, cancel it, and read the workflow's status and history.

```{note}
Every workflow endpoint requires an authenticated request, including the reads. See [](api_v3_authentication) for more information.
```

Workflow operations run through the same action layer as the admin interface, so permissions, locking, revisions, audit logs, hooks, signals, and notification emails behave exactly as when the same workflow action is taken in the admin.

## The endpoints

The same seven endpoints exist for pages, under `/pages/{page_id}/...`, and for snippets whose model inherits from `WorkflowMixin`, under `/snippets/{type}/{pk}/...` (see [](api_v3_snippets)):

| Endpoint | Body | Purpose |
| --- | --- | --- |
| `POST /pages/{page_id}/actions/workflow/submit/` | — | Submit the object for moderation |
| `POST /pages/{page_id}/actions/workflow/approve/` | `comment`, `task_state_id` | Approve the current task |
| `POST /pages/{page_id}/actions/workflow/reject/` | `comment`, `task_state_id` | Reject the current task, requesting changes |
| `POST /pages/{page_id}/actions/workflow/resume/` | — | Resume the workflow after changes were made |
| `POST /pages/{page_id}/actions/workflow/cancel/` | — | Cancel the active workflow |
| `GET /pages/{page_id}/workflow/` | — | Read the object's current workflow status |
| `GET /pages/{page_id}/workflow/history/` | — | List the object's workflow states, newest first |

Every successful response, for both the transitions and the status read, uses the same workflow status shape, so a client can re-render its workflow view from any of them.

## Submitting a workflow

`/pages/{page_id}/actions/workflow/submit/` starts the workflow assigned to the object, on its latest revision. It requires the `change` (edit) permission for the object, and that the object is not locked for the caller:

```sh
curl -X POST "https://example.com/api/v3/pages/3/actions/workflow/submit/" \
  -H "Authorization: Bearer $TOKEN"
```

A locked object returns `403`, including when it is locked because it is already in a workflow. Like the admin's "Submit for moderation" button, submitting is allowed even when the live page is unchanged: the workflow then starts on the current revision. If the object has no revision yet, one is created first from its current state.

## Approving and rejecting the current task

`/pages/{page_id}/actions/workflow/approve/` and `.../reject/` act on the workflow's current task. They require no page or snippet model permission: the caller only needs to be able to perform the action on the current task, which for `GroupApprovalTask` means membership of the task's groups. The request body accepts:

-   **`comment`**: an optional string, recorded on the task state and shown to other workflow participants.
-   **`task_state_id`**: the optional ID of the task state to act on, from `current_task_state` or the `tasks` timeline in a status response. When provided, it must match the object's current task state; otherwise the request fails with `422`. Pass it to guard against the workflow having moved on since the status was read.

The rest of the body is validated with the task's form for the action, as in the admin (see `Task.get_form_for_action` in [](custom_tasks_behavior)). For `GroupApprovalTask`, that form only has `comment`. A [custom task](custom_tasks) with extra form fields accepts them as additional keys in the body, and they are passed on to its `on_action` method. Invalid form data returns the standard `422` validation error envelope, with each error's `loc` naming the form field.

```sh
curl -X POST "https://example.com/api/v3/pages/3/actions/workflow/approve/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment": "Looks good to me", "task_state_id": 21}'
```

Approving the final task of a workflow completes it and publishes the object's revision as the caller. This requires the `publish` permission: an approver without it gets `403`, and the approval does not take effect — grant moderators publish permission, as Wagtail's own example fixtures do. Rejecting sets the workflow to "needs changes", with the comment recorded on the task state.

```{note}
Custom task actions beyond approve and reject (a `Task` subclass's own `on_action` handlers) are not exposed through the API, and are not listed in `allowed_actions`. The nested `workflow/` URL prefix keeps room for them to be added later.
```

## Resuming a workflow

`/pages/{page_id}/actions/workflow/resume/` returns a workflow in the "needs changes" state to "in progress", resubmitting the object after edits. It has no request body, and requires the `change` permission and that the object is not locked for the caller. Depending on the `WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT` setting, tasks approved on an earlier revision may need to be approved again on the new one.

## Cancelling a workflow

`/pages/{page_id}/actions/workflow/cancel/` cancels the object's active workflow. It has no request body, and requires that the caller can cancel the workflow: the user who requested it, the object's owner, or anyone who can act on the workflow's current in-progress task — provided the object is not locked by someone else.

## Reading the workflow status

`GET /pages/{page_id}/workflow/` returns the object's workflow status:

```json
{
    "workflow": {"id": 1, "name": "Moderators approval"},
    "workflow_state": {
        "id": 8,
        "status": "in_progress",
        "created_at": "2026-10-14T09:30:00Z",
        "requested_by": {"id": 4, "name": "Jane Editor"},
        "current_task_state": {
            "id": 21,
            "task": {"id": 2, "name": "Moderators approval", "type": "wagtailcore.GroupApprovalTask"},
            "status": "in_progress",
            "revision_id": 105,
            "started_at": "2026-10-14T09:30:01Z",
            "finished_at": null,
            "finished_by": null,
            "comment": ""
        },
        "task_states": [
            {
                "id": 21,
                "task": {"id": 2, "name": "Moderators approval", "type": "wagtailcore.GroupApprovalTask"},
                "status": "in_progress",
                "revision_id": 105,
                "started_at": "2026-10-14T09:30:01Z",
                "finished_at": null,
                "finished_by": null,
                "comment": ""
            }
        ],
        "tasks": [
            {
                "task": {"id": 2, "name": "Moderators approval", "type": "wagtailcore.GroupApprovalTask"},
                "task_state": {
                    "id": 21,
                    "task": {"id": 2, "name": "Moderators approval", "type": "wagtailcore.GroupApprovalTask"},
                    "status": "in_progress",
                    "revision_id": 105,
                    "started_at": "2026-10-14T09:30:01Z",
                    "finished_at": null,
                    "finished_by": null,
                    "comment": ""
                }
            },
            {"task": {"id": 3, "name": "Legal approval", "type": "wagtailcore.GroupApprovalTask"}, "task_state": null}
        ]
    },
    "allowed_actions": ["approve", "reject", "cancel"]
}
```

-   **`workflow`**: the workflow assigned to the object, or `null` when there is none (or workflows are disabled with `WAGTAIL_WORKFLOW_ENABLED`).
-   **`workflow_state`**: the object's latest workflow state, whether active or finished; `null` when the object was never submitted. The `status` field (`in_progress`, `needs_changes`, `approved`, `cancelled`) disambiguates, so a just-approved or just-cancelled workflow remains inspectable.
-   **`requested_by`**: the user who started the workflow. Users, here and in `finished_by`, are given by their `id` and display `name`: their full name if set, otherwise their username.
-   **`current_task_state`**: the task state awaiting action, or `null` when there is none.
-   **`task_states`**: the states created so far, oldest first. Each task state includes the `task` it belongs to.
-   **`tasks`**: the workflow's full task timeline. Each item pairs a `task` with its `task_state`, which is `null` for tasks that have not started yet — a moderation UI can render "Not started" / "In progress" / "Approved"… exactly like the admin's workflow dialog.
-   **`allowed_actions`**: the transitions the current user may perform right now, among `submit`, `approve`, `reject`, `resume`, and `cancel`. What is advertised is what the API accepts: after a workflow finishes or is cancelled, `submit` reappears here for users who can edit.

## Workflow history

`GET /pages/{page_id}/workflow/history/` returns a paginated list of the object's workflow states, newest first, using the same pagination envelope as every list endpoint (see [](api_v3)). Each item carries the workflow state fields above, including its `task_states` list, but without the `tasks` timeline.

## Permissions

-   **`submit`, `resume`**: the caller needs the `change` (edit) permission for the object, and the object must not be locked for them.
-   **`approve`, `reject`**: the caller needs to be able to act on the current task (for `GroupApprovalTask`, membership of the task's groups). No page or snippet model permission is required — a moderator who only belongs to the approval groups can approve and reject, and read the status.
-   **`cancel`**: the caller needs to be able to cancel the workflow — its requester, the object's owner, or a user who can act on the current in-progress task, when the object is not locked by someone else.
-   **reads** (`/workflow/`, `/workflow/history/`): any caller who can edit the object, can act on its current task, or can cancel the workflow. This is wider than the admin, so that an external moderation UI can serve approvers who hold no edit permission.

## Errors

State-machine violations return the standard validation error envelope with HTTP `422` and an error of type `workflow_state_error`:

```json
{
    "type": "about:blank",
    "title": "Unprocessable Entity",
    "status": 422,
    "detail": "Validation failed",
    "errors": [
        {"type": "workflow_state_error", "loc": [], "msg": "A workflow is already active on this object."}
    ]
}
```

The messages are:

-   Submitting with no workflow assigned to the object: "There is no active workflow assigned to this object."
-   Submitting an alias page: "This page is an alias of another page and cannot be submitted for moderation."
-   Submitting while a workflow is already active: "A workflow is already active on this object."
-   Approving or rejecting when no task is awaiting moderation, including when the task state shown to the caller is stale or no longer current (other than a `task_state_id` mismatch): "This object is not currently awaiting moderation."
-   Approving or rejecting with a `task_state_id` that is no longer current: "The provided task_state_id does not match the object's current task state."
-   Resuming when the workflow is not awaiting changes: "The workflow on this object is not awaiting changes."
-   Cancelling when there is no active workflow: "There is no active workflow on this object to cancel."

Permission failures return `403`, and a missing object `404` — with plain primary-key fetching like the other action endpoints, workflow visibility is decided by the permission gates above, not by the fetch.

Permissions are checked before the workflow state, so only callers who can read the object's workflow status receive these `422` errors; anyone else gets `403`. For example, an approver who is only a member of the current task's groups gets `403` once the workflow has moved on to a task they cannot act on.

## Settings and behaviour notes

-   Workflow transitions send the same notification emails as the admin, to the same recipients.
-   Each transition writes one audit-log entry (`wagtail.workflow.start`, `wagtail.workflow.approve`, `wagtail.workflow.reject`, `wagtail.workflow.resume`, `wagtail.workflow.cancel`), with the same payload as the admin flow.
-   With `WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH` enabled (the default), publishing an object over the API cancels any in-progress workflow on it, as it does in the admin.
-   With `WAGTAIL_WORKFLOW_ENABLED` set to `False`, submitting returns the "There is no active workflow assigned to this object." error, and the status read returns `null` workflow fields.
-   As in the admin, the workflow can be started on an unchanged live object, and approving the final task publishes the revision as the approver, which requires the `publish` permission.

## Workflow API reference

We document the full generated OpenAPI reference for every workflow endpoint, for pages and snippets, from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
