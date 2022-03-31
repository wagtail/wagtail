import wagtail.utils.models
from wagtail.models import Task

TASK_TYPES = []


def get_task_types(task_class=None):
    global TASK_TYPES
    if TASK_TYPES:
        return TASK_TYPES
    TASK_TYPES = list(
        wagtail.utils.models.get_concrete_descendants(Task, inclusive=False)
    )
    return TASK_TYPES


def publish_workflow_state(workflow_state, user=None):
    # publish the Page associated with a WorkflowState
    workflow_state.page.get_latest_revision().publish(user=user)
