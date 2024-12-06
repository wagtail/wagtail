from collections import defaultdict
from datetime import timedelta

import django_filters
from django.contrib.admin.utils import quote
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
from wagtail.admin.ui.tables import Column, DateColumn, UserColumn
from wagtail.admin.utils import get_latest_str
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
        actions = self.get_action_choices()
        if not actions:
            del self.filters["action"]
        else:
            self.filters["action"].extra["choices"] = actions

        users = self.get_users_queryset()
        if not users.exists():
            del self.filters["user"]
        else:
            self.filters["user"].extra["queryset"] = users

    def get_action_choices(self):
        return get_actions_for_filter(self.queryset)

    def get_users_queryset(self):
        return self.queryset.get_users()


class ActionColumn(Column):
    def __init__(self, *args, object, url_names, user_can_unschedule, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = object
        self.url_names = url_names
        self.user_can_unschedule = user_can_unschedule
        self.revision_enabled = isinstance(object, RevisionMixin)
        self.draftstate_enabled = isinstance(object, DraftStateMixin)

    @cached_property
    def cell_template_name(self):
        if self.revision_enabled:
            return "wagtailadmin/generic/history/action_cell.html"
        return super().cell_template_name

    def get_status(self, instance, parent_context):
        if self.draftstate_enabled:
            if (
                instance.action == "wagtail.publish"
                and instance.revision_id == self.object.live_revision_id
            ):
                return gettext("Live version")
            elif (
                instance.content_changed
                and instance.revision_id == self.object.latest_revision_id
            ):
                return gettext("Current draft")
        return None

    def get_actions(self, instance, parent_context):
        actions = []

        # Do not show the revision actions if the log entry:
        # - has no revision attached
        # - has no content changes
        # - is a "publish" action
        #   (because we want to show the options on the "edit" action instead)
        if (
            not self.revision_enabled
            or not instance.revision_id
            or not instance.content_changed
            or instance.action == "wagtail.publish"
        ):
            return actions

        if (
            isinstance(self.object, PreviewableMixin)
            and self.object.is_previewable()
            and (url_name := self.url_names.get("revisions_view"))
        ):
            url = reverse(url_name, args=(quote(self.object.pk), instance.revision_id))
            action = {"url": url, "label": gettext("Preview")}
            actions.append(action)

        if instance.revision_id == self.object.latest_revision_id:
            if url_name := self.url_names.get("edit"):
                url = reverse(url_name, args=(quote(self.object.pk),))
                action = {"url": url, "label": gettext("Edit")}
                actions.append(action)
        elif url_name := self.url_names.get("revisions_revert"):
            url = reverse(url_name, args=(quote(self.object.pk), instance.revision_id))
            action = {"url": url, "label": gettext("Review this version")}
            actions.append(action)

        if url_name := self.url_names.get("revisions_compare"):
            if instance.previous_revision_id:
                url = reverse(
                    url_name,
                    args=(
                        quote(self.object.pk),
                        instance.previous_revision_id,
                        instance.revision_id,
                    ),
                )
                action = {"url": url, "label": gettext("Compare with previous version")}
                actions.append(action)
            if instance.revision_id != self.object.latest_revision_id:
                url = reverse(
                    url_name,
                    args=(quote(self.object.pk), instance.revision_id, "latest"),
                )
                action = {"url": url, "label": gettext("Compare with current version")}
                actions.append(action)

        if (
            (url_name := self.url_names.get("revisions_unschedule"))
            and instance.revision
            and instance.revision.approved_go_live_at
            and self.user_can_unschedule
        ):
            url = reverse(url_name, args=(quote(self.object.pk), instance.revision_id))
            action = {"url": url, "label": gettext("Cancel scheduled publish")}
            actions.append(action)

        return actions

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["status"] = self.get_status(instance, parent_context)
        context["actions"] = self.get_actions(instance, parent_context)
        return context


class LogEntryUserColumn(UserColumn):
    def __init__(self, name, **kwargs):
        # Instead of accepting a blank_display_name arg, we'll make use of the
        # BaseLogEntry.user_display_name property which also handles the display
        # name for a deleted user (as the BaseLogEntry still stores the ID).
        super().__init__(name, blank_display_name=None, **kwargs)

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        if not context["display_name"]:
            context["display_name"] = instance.user_display_name
        return context


class HistoryView(PermissionCheckedMixin, BaseObjectMixin, BaseListingView):
    any_permission_required = ["add", "change", "delete"]
    page_title = gettext_lazy("History")
    header_icon = "history"
    paginate_by = 20
    filterset_class = HistoryFilterSet
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
                user_can_unschedule=self.user_can_unschedule(),
            ),
            LogEntryUserColumn("user", label=gettext_lazy("User"), width="25%"),
            DateColumn("timestamp", label=gettext_lazy("Date"), width="15%"),
        ]

    def get_base_object_queryset(self):
        queryset = super().get_base_object_queryset()
        if issubclass(queryset.model, RevisionMixin):
            return queryset.select_related("latest_revision")
        return queryset

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url_name:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        edit_url = self.get_edit_url(self.object)
        obj_name = self.get_page_subtitle()
        if edit_url:
            items.append(
                {
                    "url": edit_url,
                    "label": obj_name,
                }
            )
        items.append(
            {
                "url": "",
                "label": gettext("History"),
                "sublabel": obj_name,
            }
        )
        return self.breadcrumbs_items + items

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

    def user_can_unschedule(self):
        return self.user_has_permission("publish")

    @cached_property
    def verbose_name_plural(self):
        return BaseLogEntry._meta.verbose_name_plural

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["object"] = self.object
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


class WorkflowHistoryView(BaseObjectMixin, BaseListingView):
    template_name = "wagtailadmin/shared/workflow_history/listing.html"
    results_template_name = "wagtailadmin/shared/workflow_history/listing_results.html"
    paginate_by = 20
    index_url_name = None
    edit_url_name = None
    workflow_history_detail_url_name = None
    page_title = gettext_lazy("Workflow history")
    context_object_name = "workflow_states"

    @cached_property
    def index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    @cached_property
    def edit_url(self):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    @cached_property
    def header_buttons(self):
        buttons = []
        if self.edit_url:
            buttons.append(
                HeaderButton(gettext("Edit"), url=self.edit_url, icon_name="edit")
            )
        return buttons

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url:
            items.append(
                {
                    "url": self.index_url,
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )

        if self.edit_url:
            items.append(
                {
                    "url": self.edit_url,
                    "label": self.get_page_subtitle(),
                }
            )
        items.append(
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            }
        )

        return self.breadcrumbs_items + items

    def get_base_queryset(self):
        return (
            WorkflowState.objects.for_instance(self.object)
            .select_related("workflow", "requested_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "object": self.object,
                "workflow_history_detail_url_name": self.workflow_history_detail_url_name,
                "model_opts": self.object._meta,
            }
        )
        return context


class WorkflowHistoryDetailView(
    BaseObjectMixin, WagtailAdminTemplateMixin, TemplateView
):
    template_name = "wagtailadmin/shared/workflow_history/detail.html"
    index_url_name = None
    edit_url_name = None
    workflow_state_url_kwarg = "workflow_state_id"
    workflow_history_url_name = None
    page_title = gettext_lazy("Workflow progress")
    header_icon = "list-ul"
    object_icon = "doc-empty-inverse"

    @cached_property
    def index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    @cached_property
    def edit_url(self):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    @cached_property
    def workflow_history_url(self):
        if self.workflow_history_url_name:
            return reverse(
                self.workflow_history_url_name, args=(quote(self.object.pk),)
            )

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url:
            items.append(
                {
                    "url": self.index_url,
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        if self.edit_url:
            items.append(
                {
                    "url": self.edit_url,
                    "label": self.get_page_subtitle(),
                }
            )
        if self.workflow_history_url:
            items.append(
                {
                    "url": self.workflow_history_url,
                    "label": gettext("Workflow history"),
                }
            )
        items.append(
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            }
        )
        return self.breadcrumbs_items + items

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    @cached_property
    def header_buttons(self):
        buttons = []
        if self.edit_url:
            buttons.append(
                HeaderButton(
                    gettext("Edit / Review"),
                    url=self.edit_url,
                    icon_name="edit",
                )
            )
        return buttons

    @cached_property
    def workflow_state(self):
        return get_object_or_404(
            WorkflowState.objects.for_instance(self.object)
            .filter(id=self.kwargs[self.workflow_state_url_kwarg])
            .select_related("requested_by", "requested_by__wagtail_userprofile")
        )

    @cached_property
    def revisions(self):
        """
        Get QuerySet of all revisions that caused a task state change during this
        workflow state. It's possible that a task is rejected and then resubmitted,
        so some tasks may be repeated. All tasks that have been completed no matter
        what revision needs to be displayed on this page.
        """
        return (
            Revision.objects.for_instance(self.object)
            .select_related("user")
            .filter(
                id__in=TaskState.objects.filter(
                    workflow_state=self.workflow_state
                ).values_list("revision_id", flat=True),
            )
            .order_by("created_at")
        )

    @cached_property
    def tasks(self):
        return self.workflow_state.workflow.tasks.all()

    @cached_property
    def task_states_by_revision(self):
        """Get QuerySet of tasks completed for each revision."""
        # Fetch task states for the revisions in one query instead of one query per revision
        task_states = (
            TaskState.objects.filter(
                workflow_state=self.workflow_state,
                revision_id__in=[revision.pk for revision in self.revisions],
            )
            .prefetch_related("task", "finished_by")
            .specific()
        )
        task_states_by_revision_id = defaultdict(list)
        for task_state in task_states:
            task_states_by_revision_id[task_state.revision_id].append(task_state)

        task_states_by_revision_task = [
            (
                revision,
                {
                    task_state.task: task_state
                    for task_state in task_states_by_revision_id[revision.pk]
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
            .select_related("finished_by", "task")
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
