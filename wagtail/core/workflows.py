from wagtail.core.models import Task


TASK_TYPES = []


def get_concrete_descendants(model_class, inclusive=True):
    """Retrieves non-abstract descendants of the given model class. If `inclusive` is set to
    True, includes model_class"""
    subclasses = model_class.__subclasses__()
    if subclasses:
        for subclass in subclasses:
            yield from get_concrete_descendants(subclass)
    if inclusive and not model_class._meta.abstract:
        yield model_class


def get_task_types(task_class=None):
    global TASK_TYPES
    if TASK_TYPES:
        return TASK_TYPES
    TASK_TYPES = list(get_concrete_descendants(Task, inclusive=False))
    return TASK_TYPES


def publish_workflow_state(workflow_state, user=None):
    # publish the Page associated with a WorkflowState
    workflow_state.page.get_latest_revision().publish(user=user)
