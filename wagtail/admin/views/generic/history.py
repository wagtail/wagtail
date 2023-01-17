from datetime import timedelta

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from wagtail.admin.views.generic.base import BaseObjectMixin
from wagtail.models import Revision, TaskState, WorkflowState


class WorkflowHistoryView(BaseObjectMixin, TemplateView):
    template_name = "wagtailadmin/shared/workflow_history/index.html"
    page_kwarg = "p"
    workflow_history_url_name = None
    workflow_history_detail_url_name = None

    @cached_property
    def workflow_states(self):
        return WorkflowState.objects.for_instance(self.object).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        paginator = Paginator(self.workflow_states, per_page=20)
        workflow_states = paginator.get_page(self.request.GET.get(self.page_kwarg))

        context.update(
            {
                "object": self.object,
                "workflow_states": workflow_states,
                "workflow_history_url_name": self.workflow_history_url_name,
                "workflow_history_detail_url_name": self.workflow_history_detail_url_name,
                "model_opts": self.object._meta,
            }
        )
        return context


class WorkflowHistoryDetailView(BaseObjectMixin, TemplateView):
    template_name = "wagtailadmin/shared/workflow_history/detail.html"
    workflow_state_url_kwarg = "workflow_state_id"
    workflow_history_url_name = None

    @cached_property
    def workflow_state(self):
        return get_object_or_404(
            WorkflowState.objects.for_instance(self.object).filter(
                id=self.kwargs[self.workflow_state_url_kwarg]
            ),
        )

    @cached_property
    def revisions(self):
        """
        Get QuerySet of all revisions that have existed during this workflow state.
        It's possible that the object is edited while the workflow is running,
        so some tasks may be repeated. All tasks that have been completed no matter
        what revision needs to be displayed on this page.
        """
        return (
            Revision.objects.for_instance(self.object)
            .filter(
                id__in=TaskState.objects.filter(
                    workflow_state=self.workflow_state
                ).values_list("revision_id", flat=True),
            )
            .order_by("-created_at")
        )

    @cached_property
    def tasks(self):
        return self.workflow_state.workflow.tasks.all()

    @cached_property
    def task_states_by_revision(self):
        """Get QuerySet of tasks completed for each revision."""
        task_states_by_revision_task = [
            (
                revision,
                {
                    task_state.task: task_state
                    for task_state in TaskState.objects.filter(
                        workflow_state=self.workflow_state, revision=revision
                    )
                },
            )
            for revision in self.revisions
        ]

        # Make sure task states are always in a consistent order
        # In some cases, they can be completed in a different order to what they are defined
        task_states_by_revision = [
            (revision, [task_states_by_task.get(task, None) for task in self.tasks])
            for revision, task_states_by_task in task_states_by_revision_task
        ]

        return task_states_by_revision

    @cached_property
    def timeline(self):
        """Generate timeline."""
        completed_task_states = (
            TaskState.objects.filter(workflow_state=self.workflow_state)
            .exclude(finished_at__isnull=True)
            .exclude(status=TaskState.STATUS_CANCELLED)
        )

        timeline = [
            {
                "time": self.workflow_state.created_at,
                "action": "workflow_started",
                "workflow_state": self.workflow_state,
            }
        ]

        if self.workflow_state.status not in (
            WorkflowState.STATUS_IN_PROGRESS,
            WorkflowState.STATUS_NEEDS_CHANGES,
        ):
            last_task = completed_task_states.order_by("finished_at").last()
            if last_task:
                timeline.append(
                    {
                        "time": last_task.finished_at + timedelta(milliseconds=1),
                        "action": "workflow_completed",
                        "workflow_state": self.workflow_state,
                    }
                )

        for revision in self.revisions:
            timeline.append(
                {
                    "time": revision.created_at,
                    "action": "edited",
                    "revision": revision,
                }
            )

        for task_state in completed_task_states:
            timeline.append(
                {
                    "time": task_state.finished_at,
                    "action": "task_completed",
                    "task_state": task_state,
                }
            )

        timeline.sort(key=lambda t: t["time"])
        timeline.reverse()

        return timeline

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "object": self.object,
                "workflow_state": self.workflow_state,
                "tasks": self.tasks,
                "task_states_by_revision": self.task_states_by_revision,
                "timeline": self.timeline,
                "workflow_history_url_name": self.workflow_history_url_name,
            }
        )
        return context
