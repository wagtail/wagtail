from django.core.exceptions import PermissionDenied

from wagtail.actions.workflow import (
    WorkflowStateError,
    can_edit_instance,
    get_available_workflow_transitions,
)


def _latest_workflow_state(instance):
    return (
        instance.workflow_states.select_related(
            "workflow",
            "requested_by",
            "current_task_state__task",
            "current_task_state__finished_by",
        )
        .order_by("-created_at", "-id")
        .first()
    )


def build_workflow_status_payload(instance, user, workflow_state=None) -> dict:
    return {
        "workflow": instance.get_workflow(),
        "workflow_state": workflow_state or _latest_workflow_state(instance),
        "allowed_actions": get_available_workflow_transitions(instance, user),
    }


def check_can_view_workflow(instance, user) -> None:
    """Read gate for workflow status and history endpoints.

    Deliberately wider than the admin, which requires edit permission:
    moderation UIs must be able to serve reviewers whose only capability is
    membership of the approval task's groups - they can act on the object
    over the API, so they can read its workflow status.
    """
    if can_edit_instance(instance, user):
        return
    task_state = instance.current_workflow_task_state
    if task_state is not None and task_state.task.specific.get_actions(instance, user):
        return
    state = instance.current_workflow_state
    if state is not None and state.user_can_cancel(user):
        return
    raise PermissionDenied


def resolve_task_state(instance, task_state_id: int | None):
    workflow_state = instance.current_workflow_state
    task_state = (
        workflow_state.current_task_state if workflow_state is not None else None
    )
    if task_state is None:
        raise WorkflowStateError("This object is not currently awaiting moderation.")
    if task_state_id is not None and task_state_id != task_state.id:
        raise WorkflowStateError(
            "The provided task_state_id does not match the object's current task state."
        )
    return task_state.specific
