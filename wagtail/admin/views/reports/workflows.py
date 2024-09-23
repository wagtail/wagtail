import datetime

import django_filters
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, Q
from django.db.models.functions import Cast
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import (
    DateRangePickerWidget,
    FilteredModelChoiceFilter,
    WagtailFilterSet,
)
from wagtail.admin.utils import get_latest_str
from wagtail.admin.widgets.button import HeaderButton
from wagtail.coreutils import get_content_type_label
from wagtail.models import (
    Task,
    TaskState,
    Workflow,
    WorkflowState,
    get_default_page_content_type,
)
from wagtail.permissions import page_permission_policy
from wagtail.snippets.models import get_editable_models

from .base import ReportView


def get_requested_by_queryset(request):
    User = get_user_model()
    return User.objects.filter(
        pk__in=set(WorkflowState.objects.values_list("requested_by__pk", flat=True))
    ).order_by(User.USERNAME_FIELD)


def get_editable_page_ids_query(request):
    pages = page_permission_policy.instances_user_has_permission_for(
        request.user, "change"
    )
    # Need to cast the page ids to string because Postgres doesn't support
    # implicit type casts when querying on GenericRelations
    # https://code.djangoproject.com/ticket/16055
    # Once the issue is resolved, we can remove this function
    # and change the query to page__in=pages
    return pages.values_list(Cast("id", output_field=CharField()), flat=True)


def get_editable_content_type_ids(request):
    editable_models = get_editable_models(request.user)
    return [
        ct.id for ct in ContentType.objects.get_for_models(*editable_models).values()
    ]


class WorkflowReportFilterSet(WagtailFilterSet):
    created_at = django_filters.DateFromToRangeFilter(
        label=_("Started at"), widget=DateRangePickerWidget
    )
    reviewable = django_filters.ChoiceFilter(
        label=_("Show"),
        method="filter_reviewable",
        choices=(("true", _("Awaiting my review")),),
        empty_label=_("All"),
        widget=forms.RadioSelect,
    )
    requested_by = django_filters.ModelChoiceFilter(
        field_name="requested_by", queryset=get_requested_by_queryset
    )

    def filter_reviewable(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(
                current_task_state__in=TaskState.objects.reviewable_by(
                    self.request.user
                )
            )
        return queryset

    class Meta:
        model = WorkflowState
        fields = ["reviewable", "workflow", "status", "requested_by", "created_at"]


class WorkflowTasksReportFilterSet(WagtailFilterSet):
    started_at = django_filters.DateFromToRangeFilter(
        label=_("Started at"), widget=DateRangePickerWidget
    )
    finished_at = django_filters.DateFromToRangeFilter(
        label=_("Completed at"), widget=DateRangePickerWidget
    )
    workflow = django_filters.ModelChoiceFilter(
        field_name="workflow_state__workflow",
        queryset=Workflow.objects.all(),
        label=_("Workflow"),
    )

    # When a workflow is chosen in the 'id_workflow' selector, filter this list of tasks
    # to just the ones whose workflows attribute includes the selected workflow.
    task = FilteredModelChoiceFilter(
        queryset=Task.objects.all(),
        filter_field="id_workflow",
        filter_accessor="workflows",
    )

    reviewable = django_filters.ChoiceFilter(
        label=_("Show"),
        method="filter_reviewable",
        choices=(("true", _("Awaiting my review")),),
        empty_label=_("All"),
        widget=forms.RadioSelect,
    )

    def filter_reviewable(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(
                id__in=TaskState.objects.reviewable_by(self.request.user).values_list(
                    "id", flat=True
                )
            )
        return queryset

    class Meta:
        model = TaskState
        fields = [
            "reviewable",
            "workflow",
            "task",
            "status",
            "started_at",
            "finished_at",
        ]


class WorkflowView(ReportView):
    results_template_name = "wagtailadmin/reports/workflow_results.html"
    page_title = _("Workflows")
    header_icon = "tasks"
    filterset_class = WorkflowReportFilterSet
    index_url_name = "wagtailadmin_reports:workflow"
    index_results_url_name = "wagtailadmin_reports:workflow_results"
    permission_policy = page_permission_policy
    any_permission_required = ["add", "change", "publish"]

    export_headings = {
        "content_object.pk": _("Page/Snippet ID"),
        "content_type": _("Page/Snippet Type"),
        "content_object": _("Page/Snippet Title"),
        "get_status_display": _("Status"),
        "created_at": _("Started at"),
    }
    list_export = [
        "workflow",
        "content_object.pk",
        "content_type",
        "content_object",
        "get_status_display",
        "requested_by",
        "created_at",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.custom_field_preprocess = self.custom_field_preprocess.copy()
        self.custom_field_preprocess["content_object"] = {
            self.FORMAT_CSV: self.get_title,
            self.FORMAT_XLSX: self.get_title,
        }
        self.custom_field_preprocess["content_type"] = {
            self.FORMAT_CSV: get_content_type_label,
            self.FORMAT_XLSX: get_content_type_label,
        }

    @cached_property
    def header_buttons(self):
        return [
            HeaderButton(
                gettext("By task"),
                reverse("wagtailadmin_reports:workflow_tasks"),
                icon_name="thumbtack",
            )
        ]

    def get_title(self, content_object):
        return get_latest_str(content_object)

    def get_filename(self):
        return "workflow-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        editable_pages = Q(
            base_content_type_id=get_default_page_content_type().id,
            object_id__in=get_editable_page_ids_query(self.request),
        )

        editable_objects = Q(
            content_type_id__in=get_editable_content_type_ids(self.request)
        )

        return (
            WorkflowState.objects.filter(editable_pages | editable_objects)
            .select_related("workflow", "requested_by")
            .prefetch_related("content_object", "content_object__latest_revision")
            .order_by("-created_at")
        )

    def decorate_paginated_queryset(self, object_list):
        return [obj for obj in object_list if obj.content_object]


class WorkflowTasksView(ReportView):
    results_template_name = "wagtailadmin/reports/workflow_tasks_results.html"
    page_title = _("Workflow tasks")
    header_icon = "thumbtack"
    filterset_class = WorkflowTasksReportFilterSet
    index_url_name = "wagtailadmin_reports:workflow_tasks"
    index_results_url_name = "wagtailadmin_reports:workflow_tasks_results"
    permission_policy = page_permission_policy
    any_permission_required = ["add", "change", "publish"]

    export_headings = {
        "workflow_state.content_object.pk": _("Page/Snippet ID"),
        "workflow_state.content_type": _("Page/Snippet Type"),
        "workflow_state.content_object.__str__": _("Page/Snippet Title"),
        "get_status_display": _("Status"),
        "workflow_state.requested_by": _("Requested By"),
    }
    list_export = [
        "task",
        "workflow_state.content_object.pk",
        "workflow_state.content_type",
        "workflow_state.content_object.__str__",
        "get_status_display",
        "workflow_state.requested_by",
        "started_at",
        "finished_at",
        "finished_by",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.custom_field_preprocess = self.custom_field_preprocess.copy()
        self.custom_field_preprocess["workflow_state.content_object"] = {
            self.FORMAT_CSV: self.get_title,
            self.FORMAT_XLSX: self.get_title,
        }
        self.custom_field_preprocess["workflow_state.content_type"] = {
            self.FORMAT_CSV: get_content_type_label,
            self.FORMAT_XLSX: get_content_type_label,
        }

    @cached_property
    def header_buttons(self):
        return [
            HeaderButton(
                gettext("By workflow"),
                reverse("wagtailadmin_reports:workflow"),
                icon_name="tasks",
            )
        ]

    def get_title(self, content_object):
        return get_latest_str(content_object)

    def get_filename(self):
        return "workflow-tasks-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        editable_pages = Q(
            workflow_state__base_content_type_id=get_default_page_content_type().id,
            workflow_state__object_id__in=get_editable_page_ids_query(self.request),
        )
        editable_objects = Q(
            workflow_state__content_type_id__in=get_editable_content_type_ids(
                self.request
            )
        )
        return (
            TaskState.objects.filter(editable_pages | editable_objects)
            .select_related("workflow_state", "task")
            .prefetch_related(
                "workflow_state__content_object",
                "workflow_state__content_object__latest_revision",
            )
            .order_by("-started_at")
        )

    def decorate_paginated_queryset(self, object_list):
        return [obj for obj in object_list if obj.workflow_state.content_object]
