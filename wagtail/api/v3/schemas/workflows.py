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
        return ".".join(obj.content_type.natural_key())


class WorkflowTaskStateSchema(BaseSchema):
    id: int
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
        return list(obj.task_states.order_by("started_at", "id"))


class WorkflowStateDetailSchema(WorkflowStateSchema):
    tasks: list[WorkflowTaskTimelineItemSchema]

    @staticmethod
    def resolve_tasks(obj) -> list[dict[str, Any]]:
        # "task" is an attribute the Task model does not expose, so map the
        # all_tasks_with_state() items to the schema's field names up front.
        return [
            {"task": task, "task_state": task.task_state}
            for task in obj.all_tasks_with_state()
        ]


class WorkflowStatusSchema(Schema):
    workflow: WorkflowSummarySchema | None = None
    workflow_state: WorkflowStateDetailSchema | None = None
    allowed_actions: list[str] = []


class WorkflowTaskActionSchema(Schema):
    comment: str | None = None
    task_state_id: PositiveInt | None = None
