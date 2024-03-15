from datetime import timedelta

import django_filters
from django.contrib.admin.utils import quote, unquote
from django.core.paginator import Paginator
from django.forms import CheckboxSelectMultiple
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy
from django.views.generic import TemplateView

from wagtail.admin.filters import (
    DateRangePickerWidget,
    MultipleUserFilter,
    WagtailFilterSet,
)
from wagtail.admin.ui.tables import Column, DateColumn, InlineActionsTable, UserColumn
from wagtail.admin.views.generic.base import (
    BaseListingView,
    BaseObjectMixin,
    WagtailAdminTemplateMixin,
)
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.widgets.button import HeaderButton
from wagtail.log_actions import registry as log_registry
from wagtail.models import (
    BaseLogEntry,
    DraftStateMixin,
    PreviewableMixin,
    Revision,
    RevisionMixin,
    TaskState,
    WorkflowState,
)


def get_actions_for_filter(queryset):
    # Only return those actions used by model log entries.
    actions = set(queryset.get_actions())
    return [action for action in log_registry.get_choices() if action[0] in actions]


class HistoryFilterSet(WagtailFilterSet):
    action = django_filters.MultipleChoiceFilter(
        label=gettext_lazy("Action"),
        widget=CheckboxSelectMultiple,
        # choices are set dynamically in __init__()
    )
    user = MultipleUserFilter(
        label=gettext_lazy("User"),
        widget=CheckboxSelectMultiple,
        # queryset is set dynamically in __init__()
    )
    timestamp = django_filters.DateFromToRangeFilter(
        label=gettext_lazy("Date"), widget=DateRangePickerWidget
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["action"].extra["choices"] = get_actions_for_filter(self.queryset)
        self.filters["user"].extra["queryset"] = self.queryset.get_users()


class ActionColumn(Column):
    def __init__(self, *args, object, url_names, user_can_unschedule, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = object
        self.url_names = url_names
        self.user_can_unschedule = user_can_unschedule

    @cached_property
    def cell_template_name(self):
        if isinstance(self.object, RevisionMixin):
            return "wagtailadmin/generic/history/action_cell.html"
        return super().cell_template_name

    def get_urls(self, instance, parent_context):
        urls = {}

        # Do not show the revision actions if the log entry:
        # - has no revision attached
        # - has no content changes
        # - is a "publish" action
        #   (because we want to show the options on the "edit" action instead)
        if (
            not isinstance(self.object, RevisionMixin)
            or not instance.revision_id
            or not instance.content_changed
            or instance.action == "wagtail.publish"
        ):
            return urls

        if (
            isinstance(self.object, PreviewableMixin)
            and self.object.is_previewable()
            and (url_name := self.url_names.get("revisions_view"))
        ):
            urls["revisions_view"] = reverse(
                url_name, args=(quote(self.object.pk), instance.revision_id)
            )

        if instance.revision_id == self.object.latest_revision_id:
            if url_name := self.url_names.get("edit"):
                urls["edit"] = reverse(url_name, args=(quote(self.object.pk),))
        elif url_name := self.url_names.get("revisions_revert"):
            urls["revisions_revert"] = reverse(
                url_name, args=(quote(self.object.pk), instance.revision_id)
            )

        if url_name := self.url_names.get("revisions_compare"):
            if instance.previous_revision_id:
                urls["revisions_compare_previous"] = reverse(
                    url_name,
                    args=(
                        quote(self.object.pk),
                        instance.previous_revision_id,
                        instance.revision_id,
                    ),
                )
            if instance.revision_id != self.object.latest_revision_id:
                urls["revisions_compare_current"] = reverse(
                    url_name,
                    args=(quote(self.object.pk), instance.revision_id, "latest"),
                )

        if (
            (url_name := self.url_names.get("revisions_unschedule"))
            and instance.revision.approved_go_live_at
            and self.user_can_unschedule
        ):
            urls["revisions_unschedule"] = reverse(
                url_name,
                args=(quote(self.object.pk), instance.revision_id),
            )

        return urls

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["object"] = self.object
        context["draftstate_enabled"] = isinstance(self.object, DraftStateMixin)
        context["urls"] = self.get_urls(instance, parent_context)
        return context


class HistoryView(PermissionCheckedMixin, BaseListingView):
    any_permission_required = ["add", "change", "delete"]
    page_title = gettext_lazy("History")
    results_template_name = "wagtailadmin/generic/history_results.html"
    header_icon = "history"
    is_searchable = False
    paginate_by = 20
    filterset_class = HistoryFilterSet
    table_class = InlineActionsTable
    history_url_name = None
    history_results_url_name = None
    edit_url_name = None
    revisions_view_url_name = None
    revisions_revert_url_name = None
    revisions_compare_url_name = None
    revisions_unschedule_url_name = None

    @cached_property
    def columns(self):
        return [
            ActionColumn(
                "message",
                label=gettext_lazy("Action"),
                object=self.object,
                url_names={
                    "edit": self.edit_url_name,
                    "revisions_view": self.revisions_view_url_name,
                    "revisions_revert": self.revisions_revert_url_name,
                    "revisions_compare": self.revisions_compare_url_name,
                    "revisions_unschedule": self.revisions_unschedule_url_name,
                },
                user_can_unschedule=self.user_has_permission("publish"),
            ),
            UserColumn("user", blank_display_name="system"),
            DateColumn("timestamp", label=gettext_lazy("Date")),
        ]

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
            {
                "url": "",
                "label": gettext("History"),
                "sublabel": self.get_page_subtitle(),
            },
        ]

    @cached_property
    def header_buttons(self):
        return [
            HeaderButton(
                label=gettext("Edit"),
                url=self.get_edit_url(self.object),
                icon_name="edit",
            ),
        ]

    def get_edit_url(self, instance):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(instance.pk),))

    def get_history_url(self, instance):
        if self.history_url_name:
            return reverse(self.history_url_name, args=(quote(instance.pk),))

    def get_history_results_url(self, instance):
        if self.history_results_url_name:
            return reverse(self.history_results_url_name, args=(quote(instance.pk),))

    def get_index_url(self):  # used for pagination links
        return self.get_history_url(self.object)

    def get_index_results_url(self):
        return self.get_history_results_url(self.object)

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["object"] = self.object
        context["model_opts"] = BaseLogEntry._meta
        return context

    def get_base_queryset(self):
        queryset = log_registry.get_logs_for_instance(self.object)
        return self._annotate_queryset(queryset)

    def _annotate_queryset(self, queryset):
        queryset = queryset.select_related("user", "user__wagtail_userprofile")
        if isinstance(self.object, RevisionMixin):
            queryset = queryset.select_related("revision").annotate(
                previous_revision_id=Revision.objects.previous_revision_id_subquery(),
            )
        return queryset

    def get_filterset_kwargs(self):
        # Pass custom queryset so the FilterSet can use it when initialising the
        # filters, instead of using the default model.objects.all() queryset.
        kwargs = super().get_filterset_kwargs()
        kwargs["queryset"] = self.get_base_queryset()
        return kwargs


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
