from datetime import timedelta

import django_filters
from django.contrib.admin.utils import unquote
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy
from django.views.generic import TemplateView

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.ui.tables import Column, DateColumn, InlineActionsTable, UserColumn
from wagtail.admin.views.generic.base import BaseObjectMixin, WagtailAdminTemplateMixin
from wagtail.admin.views.generic.models import IndexView
from wagtail.log_actions import registry as log_registry
from wagtail.models import (
    DraftStateMixin,
    ModelLogEntry,
    Revision,
    TaskState,
    WorkflowState,
)


def get_actions_for_filter():
    # Only return those actions used by model log entries.
    actions = set(ModelLogEntry.objects.all().get_actions())
    return [action for action in log_registry.get_choices() if action[0] in actions]


class HistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(
        label=gettext_lazy("Action"),
        # choices are set dynamically in __init__()
    )
    user = django_filters.ModelChoiceFilter(
        label=gettext_lazy("User"),
        field_name="user",
        queryset=lambda request: ModelLogEntry.objects.all().get_users(),
    )
    timestamp = django_filters.DateFromToRangeFilter(
        label=gettext_lazy("Date"), widget=DateRangePickerWidget
    )

    class Meta:
        model = ModelLogEntry
        fields = ["action", "user", "timestamp"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["action"].extra["choices"] = get_actions_for_filter()


class HistoryView(IndexView):
    any_permission_required = ["add", "change", "delete"]
    page_title = gettext_lazy("History")
    results_template_name = "wagtailadmin/generic/history_results.html"
    header_icon = "history"
    is_searchable = False
    paginate_by = 20
    filterset_class = HistoryReportFilterSet
    table_class = InlineActionsTable

    def setup(self, request, *args, pk, **kwargs):
        self.pk = pk
        self.object = self.get_object()
        super().setup(request, *args, **kwargs)

    def get_object(self):
        object = get_object_or_404(self.model, pk=unquote(self.pk))
        if isinstance(object, DraftStateMixin):
            return object.get_latest_revision_as_object()
        return object

    def get_page_subtitle(self):
        return str(self.object)

    def get_columns(self):
        return [
            Column("message", label=gettext("Action")),
            UserColumn("user", blank_display_name="system"),
            DateColumn("timestamp", label=gettext("Date")),
        ]

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items + [
            {
                "url": reverse(self.index_url_name),
                "label": capfirst(self.model._meta.verbose_name_plural),
            },
            {
                "url": self.get_edit_url(self.object),
                "label": str(self.object),
            },
            {"url": "", "label": gettext("History")},
        ]

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["object"] = self.object
        context["header_action_url"] = self.get_edit_url(self.object)
        context["header_action_label"] = gettext("Edit this %(model_name)s") % {
            "model_name": self.model._meta.verbose_name
        }
        context["header_action_icon"] = "edit"
        return context

    def get_base_queryset(self):
        return log_registry.get_logs_for_instance(self.object).select_related(
            "revision", "user", "user__wagtail_userprofile"
        )


class WorkflowHistoryView(BaseObjectMixin, WagtailAdminTemplateMixin, TemplateView):
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


class WorkflowHistoryDetailView(
    BaseObjectMixin, WagtailAdminTemplateMixin, TemplateView
):
    template_name = "wagtailadmin/shared/workflow_history/detail.html"
    workflow_state_url_kwarg = "workflow_state_id"
    workflow_history_url_name = None
    page_title = gettext_lazy("Workflow progress")
    header_icon = "list-ul"
    object_icon = "doc-empty-inverse"

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
                    ).specific()
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
                "object_icon": self.object_icon,
                "workflow_state": self.workflow_state,
                "tasks": self.tasks,
                "task_states_by_revision": self.task_states_by_revision,
                "timeline": self.timeline,
                "workflow_history_url_name": self.workflow_history_url_name,
            }
        )
        return context
