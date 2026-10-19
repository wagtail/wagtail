from datetime import datetime
from typing import Any, Literal

from ninja import Schema
from pydantic import PositiveInt

from wagtail.actions.workflow import get_available_workflow_transitions

from .base import BaseSchema


class WorkflowUserSummarySchema(Schema):
    id: str
    username: str

    @staticmethod
    def resolve_id(obj) -> str:
        return str(obj.pk)

    @staticmethod
    def resolve_username(obj) -> str:
        return obj.get_username()


class WorkflowSummarySchema(Schema):
    id: int
    name: str


class WorkflowTaskSummarySchema(Schema):
    id: int
    name: str
    type: str

    @staticmethod
    def resolve_type(obj) -> str:
        content_type = obj.content_type
        if model := content_type.model_class():
            return model._meta.label
        return f"{content_type.app_label}.{content_type.model}"


class WorkflowTaskStateSchema(BaseSchema):
    id: int
    task: WorkflowTaskSummarySchema
    status: Literal["in_progress", "approved", "rejected", "skipped", "cancelled"]
    revision_id: int
    started_at: datetime
    finished_at: datetime | None = None
    finished_by: WorkflowUserSummarySchema | None = None
    comment: str


class WorkflowTaskTimelineItemSchema(Schema):
    task: WorkflowTaskSummarySchema
    task_state: WorkflowTaskStateSchema | None = None


class WorkflowStateSchema(BaseSchema):
    id: int
    workflow: WorkflowSummarySchema
    status: Literal["in_progress", "needs_changes", "approved", "cancelled"]
    created_at: datetime
    requested_by: WorkflowUserSummarySchema | None = None
    current_task_state: WorkflowTaskStateSchema | None = None
    task_states: list[WorkflowTaskStateSchema]

    @staticmethod
    def resolve_task_states(obj) -> list[WorkflowTaskStateSchema]:
        # Populated by WorkflowStateQuerySet.prefetch_task_states().
        return obj._prefetched_task_states


class WorkflowStateDetailSchema(WorkflowStateSchema):
    tasks: list[WorkflowTaskTimelineItemSchema]

    @staticmethod
    def resolve_tasks(obj) -> list[dict[str, Any]]:
        # "task" is an attribute the Task model does not expose, so map the
        # all_tasks_with_state() items to the schema's field names up front.
        tasks = obj.all_tasks_with_state()
        for task in tasks:
            if task.task_state is not None:
                task.task_state.task = task
        return [{"task": task, "task_state": task.task_state} for task in tasks]


class WorkflowStatusSchema(Schema):
    workflow: WorkflowSummarySchema | None = None
    workflow_state: WorkflowStateDetailSchema | None = None
    allowed_actions: list[str] = []

    @staticmethod
    def resolve_workflow(obj):
        return obj.get_workflow()

    @staticmethod
    def resolve_workflow_state(obj):
        return (
            obj.workflow_states.prefetch_task_states()
            .order_by("-created_at", "-id")
            .first()
        )

    @staticmethod
    def resolve_allowed_actions(obj, context: dict) -> list[str]:
        return get_available_workflow_transitions(obj, context["request"].user)


class WorkflowTaskActionSchema(Schema):
    comment: str | None = None
    task_state_id: PositiveInt | None = None
