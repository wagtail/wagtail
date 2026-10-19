from datetime import datetime
from typing import Any, Literal

from ninja import Schema
from pydantic import PositiveInt

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
        # History requests prefetch task states onto `_prefetched_task_states`
        # (already ordered); `all()`/order_by would clone the related manager and
        # discard that prefetch cache, so consume the attribute when present and
        # fall back to the ordered manager path for non-prefetched states (status
        # endpoint).
        task_states = getattr(obj, "_prefetched_task_states", None)
        if task_states is None:
            task_states = obj.task_states.select_related("task__content_type").order_by(
                "started_at", "id"
            )
        return list(task_states)


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


class WorkflowTaskActionSchema(Schema):
    comment: str | None = None
    task_state_id: PositiveInt | None = None
