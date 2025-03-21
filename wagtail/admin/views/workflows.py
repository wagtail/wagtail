import django_filters
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Prefetch
from django.db.models.functions import Lower
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.filters import (
    MultipleContentTypeFilter,
    WagtailFilterSet,
)
from wagtail.admin.forms.workflows import (
    TaskChooserSearchForm,
    WorkflowContentTypeForm,
    WorkflowPagesFormSet,
    get_task_form_class,
    get_workflow_edit_handler,
)
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import BaseColumn, Column, TitleColumn
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.admin.views.generic.base import BaseListingView
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.views.pages.listing import PageListingMixin
from wagtail.coreutils import resolve_model_string
from wagtail.models import (
    Page,
    Task,
    TaskState,
    Workflow,
    WorkflowState,
    WorkflowTask,
)
from wagtail.permissions import (
    page_permission_policy,
    task_permission_policy,
    workflow_permission_policy,
)
from wagtail.snippets.models import get_workflow_enabled_models
from wagtail.workflows import get_task_types

task_permission_checker = PermissionPolicyChecker(task_permission_policy)


class WorkflowTitleColumn(TitleColumn):
    cell_template_name = "wagtailadmin/workflows/includes/workflow_title_cell.html"


class WorkflowUsedByColumn(TitleColumn):
    cell_template_name = "wagtailadmin/workflows/includes/workflow_used_by_cell.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["workflow_enabled_models"] = get_workflow_enabled_models()
        return context


class WorkflowTasksColumn(BaseColumn):
    cell_template_name = "wagtailadmin/workflows/includes/workflow_tasks_cell.html"
    num_tasks = 5

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["tasks"] = instance.workflow_tasks.all()[: self.num_tasks]
        context["extra_count"] = instance.workflow_tasks.count() - self.num_tasks
        return context


class BaseWorkflowFilterSet(WagtailFilterSet):
    show_disabled = django_filters.ChoiceFilter(
        label=_("Show disabled"),
        method="filter_show_disabled",
        choices=(("true", _("Yes")), ("false", _("No"))),
        widget=forms.RadioSelect,
        empty_label=None,
        initial="false",
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        if data is not None:
            if data.get("show_disabled") is None:
                filter = self.base_filters["show_disabled"]
                data = data.copy()
                data["show_disabled"] = filter.extra["initial"]
        super().__init__(data, queryset, request=request, prefix=prefix)

    def filter_show_disabled(self, queryset, name, value):
        if value == "true":
            return queryset
        return queryset.filter(active=True)


class WorkflowFilterSet(BaseWorkflowFilterSet):
    class Meta:
        model = Workflow
        fields = []


class Index(IndexView):
    permission_policy = workflow_permission_policy
    model = Workflow
    context_object_name = "workflows"
    template_name = "wagtailadmin/workflows/index.html"
    results_template_name = "wagtailadmin/workflows/index_results.html"
    add_url_name = "wagtailadmin_workflows:add"
    edit_url_name = "wagtailadmin_workflows:edit"
    index_url_name = "wagtailadmin_workflows:index"
    index_results_url_name = "wagtailadmin_workflows:index_results"
    page_title = _("Workflows")
    add_item_label = _("Add a workflow")
    header_icon = "tasks"
    columns = [
        WorkflowTitleColumn(
            "name",
            label=_("Name"),
            url_name="wagtailadmin_workflows:edit",
            width="25%",
            sort_key="name",
        ),
        WorkflowUsedByColumn(
            "usage",
            label=_("Used by"),
            url_name="wagtailadmin_workflows:usage",
            width="15%",
        ),
        WorkflowTasksColumn("tasks", label=_("Tasks")),
    ]
    default_ordering = "name"
    search_fields = ["name"]
    filterset_class = WorkflowFilterSet
    paginate_by = 20

    def show_disabled(self):
        return self.filters.form.cleaned_data.get("show_disabled") == "true"

    def get_base_queryset(self):
        queryset = super().get_base_queryset()
        queryset = queryset.annotate(content_types=Count("workflow_content_types"))
        return queryset.prefetch_related(
            "workflow_pages",
            "workflow_pages__page",
            "workflow_tasks",
            "workflow_tasks__task",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["showing_disabled"] = self.show_disabled()
        return context


class Create(CreateView):
    permission_policy = workflow_permission_policy
    model = Workflow
    page_title = _("New workflow")
    template_name = "wagtailadmin/workflows/create.html"
    success_message = _("Workflow '%(object)s' created.")
    add_url_name = "wagtailadmin_workflows:add"
    edit_url_name = "wagtailadmin_workflows:edit"
    index_url_name = "wagtailadmin_workflows:index"
    header_icon = "tasks"
    edit_handler = None

    def get_edit_handler(self):
        if not self.edit_handler:
            self.edit_handler = get_workflow_edit_handler()
        return self.edit_handler

    def get_form_class(self):
        return self.get_edit_handler().get_form_class()

    def get_pages_formset(self):
        if self.request.method == "POST":
            return WorkflowPagesFormSet(
                self.request.POST, instance=self.object, prefix="pages"
            )
        else:
            return WorkflowPagesFormSet(instance=self.object, prefix="pages")

    def get_content_type_form(self):
        if self.request.method == "POST":
            return WorkflowContentTypeForm(self.request.POST, workflow=self.object)
        else:
            return WorkflowContentTypeForm(workflow=self.object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        bound_panel = self.edit_handler.get_bound_panel(
            form=form, instance=form.instance, request=self.request
        )
        pages_formset = self.get_pages_formset()

        context["edit_handler"] = bound_panel
        context["pages_formset"] = pages_formset
        context["has_workflow_enabled_models"] = bool(get_workflow_enabled_models())
        context["content_type_form"] = self.get_content_type_form()
        context["media"] = form.media + bound_panel.media + pages_formset.media
        return context

    def form_valid(self, form):
        self.form = form

        with transaction.atomic():
            self.object = self.save_instance()

            pages_formset = self.get_pages_formset()
            content_type_form = self.get_content_type_form()
            if pages_formset.is_valid() and content_type_form.is_valid():
                pages_formset.save()
                content_type_form.save()

                success_message = self.get_success_message(self.object)
                if success_message is not None:
                    messages.success(
                        self.request,
                        success_message,
                        buttons=[
                            messages.button(
                                reverse(self.edit_url_name, args=(self.object.id,)),
                                _("Edit"),
                            )
                        ],
                    )
                return redirect(self.get_success_url())

            else:
                transaction.set_rollback(True)

        return self.form_invalid(form)


class Edit(EditView):
    permission_policy = workflow_permission_policy
    model = Workflow
    page_title = _("Editing workflow")
    template_name = "wagtailadmin/workflows/edit.html"
    success_message = _("Workflow '%(object)s' updated.")
    add_url_name = "wagtailadmin_workflows:add"
    edit_url_name = "wagtailadmin_workflows:edit"
    delete_url_name = "wagtailadmin_workflows:disable"
    delete_item_label = _("Disable")
    index_url_name = "wagtailadmin_workflows:index"
    enable_item_label = _("Enable")
    enable_url_name = "wagtailadmin_workflows:enable"
    header_icon = "tasks"
    header_more_buttons = []
    edit_handler = None
    MAX_PAGES = 5

    def get_edit_handler(self):
        if not self.edit_handler:
            self.edit_handler = get_workflow_edit_handler()
        return self.edit_handler

    def get_form_class(self):
        return self.get_edit_handler().get_form_class()

    def get_pages_formset(self):
        if self.request.method == "POST":
            return WorkflowPagesFormSet(
                self.request.POST, instance=self.get_object(), prefix="pages"
            )
        else:
            return WorkflowPagesFormSet(instance=self.get_object(), prefix="pages")

    def get_content_type_form(self):
        if self.request.method == "POST":
            return WorkflowContentTypeForm(self.request.POST, workflow=self.object)
        else:
            return WorkflowContentTypeForm(workflow=self.object)

    def get_paginated_pages(self):
        # Get the (paginated) list of Pages to which this Workflow is assigned.
        pages = Page.objects.filter(workflowpage__workflow=self.get_object())
        pages.paginator = Paginator(pages, self.MAX_PAGES)
        page_number = int(self.request.GET.get("p", 1))
        paginated_pages = pages.paginator.page(page_number)
        return paginated_pages

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        bound_panel = self.edit_handler.get_bound_panel(
            form=form, instance=form.instance, request=self.request
        )
        pages_formset = self.get_pages_formset()
        context["edit_handler"] = bound_panel
        context["pages"] = self.get_paginated_pages()
        context["has_workflow_enabled_models"] = bool(get_workflow_enabled_models())
        context["content_type_form"] = self.get_content_type_form()
        context["can_disable"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "delete")
        ) and self.object.active
        context["can_enable"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "add")
        ) and not self.object.active
        context["media"] = bound_panel.media + form.media

        # Only add the pages_formset if the workflow is active
        if self.object.active:
            pages_formset = self.get_pages_formset()
            context["pages_formset"] = pages_formset
            context["media"] += pages_formset.media

        return context

    @property
    def get_enable_url(self):
        return reverse(self.enable_url_name, args=(self.object.pk,))

    @transaction.atomic()
    def form_valid(self, form):
        self.form = form

        with transaction.atomic():
            self.object = self.save_instance()
            successful = True

            # Save pages formset and content type form
            # Note: These are hidden when the workflow is inactive
            if self.object.active:
                pages_formset = self.get_pages_formset()
                content_type_form = self.get_content_type_form()
                if pages_formset.is_valid() and content_type_form.is_valid():
                    pages_formset.save()
                    content_type_form.save()
                else:
                    transaction.set_rollback(True)
                    successful = False

            if successful:
                success_message = self.get_success_message()
                if success_message is not None:
                    messages.success(
                        self.request,
                        success_message,
                        buttons=[
                            messages.button(
                                reverse(self.edit_url_name, args=(self.object.id,)),
                                _("Edit"),
                            )
                        ],
                    )
                return redirect(self.get_success_url())

        return self.form_invalid(form)


class Disable(DeleteView):
    permission_policy = workflow_permission_policy
    model = Workflow
    page_title = _("Disable workflow")
    template_name = "wagtailadmin/workflows/confirm_disable.html"
    success_message = _("Workflow '%(object)s' disabled.")
    add_url_name = "wagtailadmin_workflows:add"
    edit_url_name = "wagtailadmin_workflows:edit"
    delete_url_name = "wagtailadmin_workflows:disable"
    index_url_name = "wagtailadmin_workflows:index"
    header_icon = "tasks"

    @property
    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.kwargs["pk"],))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        states_in_progress = WorkflowState.objects.filter(
            workflow=self.object, status=WorkflowState.STATUS_IN_PROGRESS
        ).count()
        if states_in_progress:
            context["warning_message"] = ngettext(
                "This workflow is in progress on %(states_in_progress)d page/snippet. Disabling this workflow will cancel moderation on this page/snippet.",
                "This workflow is in progress on %(states_in_progress)d pages/snippets. Disabling this workflow will cancel moderation on these pages/snippets.",
                states_in_progress,
            ) % {
                "states_in_progress": states_in_progress,
            }
        return context

    def delete_action(self):
        self.object.deactivate(user=self.request.user)


class WorkflowUsageView(PageListingMixin, PermissionCheckedMixin, BaseListingView):
    permission_policy = workflow_permission_policy
    any_permission_required = {"add", "change", "delete", "view"}
    pk_url_kwarg = "pk"
    index_url_name = "wagtailadmin_workflows:usage"
    index_results_url_name = "wagtailadmin_workflows:usage_results"
    paginate_by = 20
    header_icon = "tasks"
    page_title = _("Usage")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        # We set workflow_permission_policy as the main permission policy for this view
        # for consistency with the other workflow views. However, since we are listing
        # page objects in this view, we want to ensure the user has a page permission.
        if not page_permission_policy.user_has_any_permission(
            request.user,
            {"add", "change", "publish", "bulk_delete", "lock", "unlock"},
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_page_subtitle(self):
        return self.object.name

    def get_breadcrumbs_items(self):
        title = self.get_page_title()
        subtitle = self.get_page_subtitle()
        return self.breadcrumbs_items + [
            {
                "url": reverse("wagtailadmin_workflows:index"),
                "label": capfirst(Workflow._meta.verbose_name_plural),
            },
            {
                "url": reverse("wagtailadmin_workflows:edit", args=(self.object.pk,)),
                "label": subtitle,
            },
            {"url": "", "label": title, "sublabel": subtitle},
        ]

    def get_index_url(self):
        return reverse(self.index_url_name, args=(self.object.pk,))

    def get_index_results_url(self):
        return reverse(self.index_results_url_name, args=(self.object.pk,))

    def get_object(self):
        return get_object_or_404(Workflow, id=self.kwargs.get(self.pk_url_kwarg))

    def get_base_queryset(self):
        editable_pages = page_permission_policy.instances_user_has_permission_for(
            self.request.user, "change"
        ).filter(depth__gt=1)
        pages = self.object.all_pages() & editable_pages
        pages = self.annotate_queryset(pages)
        return pages


@require_POST
def enable_workflow(request, pk):
    # Reactivate an inactive workflow
    workflow = get_object_or_404(Workflow, id=pk)

    # Check permissions
    if not workflow_permission_policy.user_has_permission(request.user, "add"):
        raise PermissionDenied

    # Set workflow to active if inactive
    if not workflow.active:
        workflow.active = True
        workflow.save()
        messages.success(
            request,
            _("Workflow '%(workflow_name)s' enabled.")
            % {"workflow_name": workflow.name},
        )

    # Redirect
    redirect_to = request.POST.get("next", None)
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to, allowed_hosts={request.get_host()}
    ):
        return redirect(redirect_to)
    else:
        return redirect("wagtailadmin_workflows:edit", workflow.id)


@require_POST
def remove_workflow(request, page_pk, workflow_pk=None):
    # Remove a workflow from a page (specifically a single workflow if workflow_pk is set)
    # Get the page
    page = get_object_or_404(Page, id=page_pk)

    # Check permissions
    if not workflow_permission_policy.user_has_permission(request.user, "change"):
        raise PermissionDenied

    if hasattr(page, "workflowpage"):
        # If workflow_pk is set, this will only remove the workflow if it its pk matches - this prevents accidental
        # removal of the wrong workflow via a workflow edit page if the page listing is out of date
        if not workflow_pk or workflow_pk == page.workflowpage.workflow.pk:
            page.workflowpage.delete()
            messages.success(
                request,
                _("Workflow removed from Page '%(page_title)s'.")
                % {"page_title": page.get_admin_display_title()},
            )

    # Redirect
    redirect_to = request.POST.get("next", None)
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to, allowed_hosts={request.get_host()}
    ):
        return redirect(redirect_to)
    else:
        return redirect("wagtailadmin_explore", page.id)


class TaskTitleColumn(TitleColumn):
    cell_template_name = "wagtailadmin/workflows/includes/task_title_cell.html"


class TaskUsageColumn(Column):
    cell_template_name = "wagtailadmin/workflows/includes/task_usage_cell.html"


class TaskFilterSet(BaseWorkflowFilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        task_types = get_task_types()
        ct_ids = [
            ct.id for ct in ContentType.objects.get_for_models(*task_types).values()
        ]
        if len(task_types) > 1:
            self.filters["content_type"] = MultipleContentTypeFilter(
                label=_("Type"),
                widget=forms.CheckboxSelectMultiple,
                queryset=lambda request: ContentType.objects.filter(pk__in=ct_ids),
                field_name="content_type",
            )

    class Meta:
        model = Task
        fields = []


class TaskIndex(IndexView):
    permission_policy = task_permission_policy
    model = Task
    context_object_name = "tasks"
    template_name = "wagtailadmin/workflows/task_index.html"
    results_template_name = "wagtailadmin/workflows/task_index_results.html"
    add_url_name = "wagtailadmin_workflows:select_task_type"
    edit_url_name = "wagtailadmin_workflows:edit_task"
    index_url_name = "wagtailadmin_workflows:task_index"
    index_results_url_name = "wagtailadmin_workflows:task_index_results"
    page_title = _("Workflow tasks")
    add_item_label = _("New workflow task")
    header_icon = "thumbtack"
    columns = [
        TaskTitleColumn(
            "name",
            label=_("Name"),
            url_name="wagtailadmin_workflows:edit_task",
            sort_key="name",
        ),
        Column("type", label=_("Type"), accessor="get_verbose_name", width="25%"),
        TaskUsageColumn(
            "usage", label=_("Used on"), accessor="_active_workflows", width="25%"
        ),
    ]
    default_ordering = "name"
    search_fields = ["name"]
    filterset_class = TaskFilterSet
    paginate_by = 50

    def show_disabled(self):
        return self.filters.form.cleaned_data.get("show_disabled") == "true"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .specific()
            .prefetch_related(
                Prefetch(
                    "workflow_tasks",
                    queryset=WorkflowTask.objects.filter(
                        workflow__active=True
                    ).select_related("workflow"),
                    to_attr="_active_workflows",
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["showing_disabled"] = self.show_disabled()
        return context


def select_task_type(request):
    if not task_permission_policy.user_has_permission(request.user, "add"):
        raise PermissionDenied

    task_types = [
        (
            model.get_verbose_name(),
            model._meta.app_label,
            model._meta.model_name,
            model.get_description(),
        )
        for model in get_task_types()
    ]
    # sort by lower-cased version of verbose name
    task_types.sort(key=lambda task_type: task_type[0].lower())

    if len(task_types) == 1:
        # Only one task type is available - redirect straight to the create form rather than
        # making the user choose
        verbose_name, app_label, model_name, description = task_types[0]
        return redirect("wagtailadmin_workflows:add_task", app_label, model_name)

    return render(
        request,
        "wagtailadmin/workflows/select_task_type.html",
        {
            "task_types": task_types,
            "icon": "thumbtack",
            "title": _("Workflows"),
        },
    )


class CreateTask(CreateView):
    permission_policy = task_permission_policy
    page_title = _("New workflow task")
    template_name = "wagtailadmin/workflows/create_task.html"
    success_message = _("Task '%(object)s' created.")
    add_url_name = "wagtailadmin_workflows:add_task"
    edit_url_name = "wagtailadmin_workflows:edit_task"
    index_url_name = "wagtailadmin_workflows:task_index"
    header_icon = "thumbtack"

    @cached_property
    def model(self):
        try:
            content_type = ContentType.objects.get_by_natural_key(
                self.kwargs["app_label"], self.kwargs["model_name"]
            )
        except (ContentType.DoesNotExist, AttributeError):
            raise Http404

        # Get class
        model = content_type.model_class()

        # Make sure the class is a descendant of Task
        if not issubclass(model, Task) or model is Task:
            raise Http404

        return model

    def get_form_class(self):
        return get_task_form_class(self.model)

    def get_add_url(self):
        return reverse(
            self.add_url_name,
            kwargs={
                "app_label": self.kwargs.get("app_label"),
                "model_name": self.kwargs.get("model_name"),
            },
        )

    def get_breadcrumbs_items(self):
        # Use the base Task class instead of the specific class for the index view
        items = [
            {
                "url": reverse(self.index_url_name),
                "label": capfirst(Task._meta.verbose_name_plural),
            },
            {
                "url": "",
                "label": _("New: %(model_name)s")
                % {"model_name": capfirst(self.model._meta.verbose_name)},
            },
        ]
        return self.breadcrumbs_items + items


class EditTask(EditView):
    permission_policy = task_permission_policy
    template_name = "wagtailadmin/workflows/edit_task.html"
    success_message = _("Task '%(object)s' updated.")
    add_url_name = "wagtailadmin_workflows:select_task_type"
    edit_url_name = "wagtailadmin_workflows:edit_task"
    delete_url_name = "wagtailadmin_workflows:disable_task"
    index_url_name = "wagtailadmin_workflows:task_index"
    delete_item_label = _("Disable")
    enable_item_label = _("Enable")
    enable_url_name = "wagtailadmin_workflows:enable_task"
    header_icon = "thumbtack"
    header_more_buttons = []

    @cached_property
    def model(self):
        return type(self.get_object())

    @cached_property
    def page_title(self):
        return _("Editing %(task_type)s") % {
            "task_type": self.get_object().content_type.name
        }

    def get_queryset(self):
        if self.queryset is None:
            return Task.objects.all()

    def get_object(self, queryset=None):
        return super().get_object().specific

    def get_form_class(self):
        return get_task_form_class(self.model, for_edit=True)

    def get_breadcrumbs_items(self):
        # Use the base Task class instead of the specific class
        items = [
            {
                "url": reverse(self.index_url_name),
                "label": capfirst(Task._meta.verbose_name_plural),
            },
            {"url": "", "label": str(self.object)},
        ]
        return self.breadcrumbs_items + items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_disable"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "delete")
        ) and self.object.active
        context["can_enable"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "add")
        ) and not self.object.active

        # TODO: add warning msg when there are pages/snippets currently on this task in a workflow, add interaction like resetting task state when saved
        return context

    @property
    def get_enable_url(self):
        return reverse(self.enable_url_name, args=(self.object.pk,))


class DisableTask(DeleteView):
    permission_policy = task_permission_policy
    model = Task
    page_title = _("Disable task")
    template_name = "wagtailadmin/workflows/confirm_disable_task.html"
    success_message = _("Task '%(object)s' disabled.")
    add_url_name = "wagtailadmin_workflows:add_task"
    edit_url_name = "wagtailadmin_workflows:edit_task"
    delete_url_name = "wagtailadmin_workflows:disable_task"
    index_url_name = "wagtailadmin_workflows:task_index"
    header_icon = "thumbtack"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        states_in_progress = TaskState.objects.filter(
            status=TaskState.STATUS_IN_PROGRESS, task=self.get_object().pk
        ).count()
        if states_in_progress:
            context["warning_message"] = ngettext(
                "This task is in progress on %(states_in_progress)d page/snippet. Disabling this task will cause it to be skipped in the moderation workflow and not be listed for selection when editing a workflow.",
                "This task is in progress on %(states_in_progress)d pages/snippets. Disabling this task will cause it to be skipped in the moderation workflow and not be listed for selection when editing a workflow.",
                states_in_progress,
            ) % {
                "states_in_progress": states_in_progress,
            }
        return context

    @property
    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.kwargs["pk"],))

    def delete_action(self):
        self.object.deactivate(user=self.request.user)


@require_POST
def enable_task(request, pk):
    # Reactivate an inactive task
    task = get_object_or_404(Task, id=pk)

    # Check permissions
    if not task_permission_policy.user_has_permission(request.user, "add"):
        raise PermissionDenied

    # Set workflow to active if inactive
    if not task.active:
        task.active = True
        task.save()
        messages.success(
            request, _("Task '%(task_name)s' enabled.") % {"task_name": task.name}
        )

    # Redirect
    redirect_to = request.POST.get("next", None)
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to, allowed_hosts={request.get_host()}
    ):
        return redirect(redirect_to)
    else:
        return redirect("wagtailadmin_workflows:edit_task", task.id)


def get_task_chosen_response(request, task):
    """
    helper function: given a task, return the response indicating that it has been chosen
    """
    result_data = {
        "id": task.id,
        "name": task.name,
        "edit_url": reverse("wagtailadmin_workflows:edit_task", args=[task.id]),
    }
    return render_modal_workflow(
        request,
        None,
        None,
        None,
        json_data={"step": "task_chosen", "result": result_data},
    )


class BaseTaskChooserView(TemplateView):
    def dispatch(self, request):
        self.task_models = get_task_types()
        self.can_create = (
            task_permission_policy.user_has_permission(request.user, "add")
            and len(self.task_models) != 0
        )
        return super().dispatch(request)

    def get_create_model(self):
        """
        To be called after dispatch(); returns the model to use for a new task if one is known
        (either from being the only available task mode, or from being specified in the URL as create_model)
        """
        if self.can_create:
            if len(self.task_models) == 1:
                return self.task_models[0]

            elif "create_model" in self.request.GET:
                create_model = resolve_model_string(self.request.GET["create_model"])

                if create_model not in self.task_models:
                    raise Http404

                return create_model

    def get_create_form_class(self):
        """
        To be called after dispatch(); returns the form class for creating a new task
        """
        self.create_model = self.get_create_model()
        if self.create_model:
            return get_task_form_class(self.create_model)
        else:
            return None

    def get_create_form(self):
        """
        To be called after dispatch(); returns a blank create form, or None if not available
        """
        create_form_class = self.get_create_form_class()
        if create_form_class:
            return create_form_class(prefix="create-task")

    def get_task_type_options(self):
        """
        To be called after dispatch(); returns the task types list for the "select task type" view
        """
        task_types = [
            (
                model.get_verbose_name(),
                model._meta.app_label,
                model._meta.model_name,
                model.get_description(),
            )
            for model in self.task_models
        ]
        # sort by lower-cased version of verbose name
        task_types.sort(key=lambda task_type: task_type[0].lower())

        return task_types

    def get_task_type_filter_choices(self):
        """
        To be called after dispatch(); returns the list of task type choices for filter on "existing task" tab
        """
        task_type_choices = [
            (model, model.get_verbose_name()) for model in self.task_models
        ]
        task_type_choices.sort(key=lambda task_type: task_type[1].lower())
        return task_type_choices

    def get_form_js_context(self):
        return {}

    def get_task_listing_context_data(self):
        search_form = TaskChooserSearchForm(
            self.request.GET, task_type_choices=self.get_task_type_filter_choices()
        )
        tasks = all_tasks = search_form.task_model.objects.filter(active=True).order_by(
            Lower("name")
        )
        q = ""

        if search_form.is_searching():
            # Note: I decided not to use wagtailsearch here. This is because
            # wagtailsearch creates a new index for each model you make
            # searchable and this might affect someone's quota. I doubt there
            # would ever be enough tasks to require using anything more than
            # an icontains anyway.
            q = search_form.cleaned_data["q"]
            tasks = tasks.filter(name__icontains=q)

        # Pagination
        paginator = Paginator(tasks, per_page=10)
        tasks = paginator.get_page(self.request.GET.get("p"))

        return {
            "search_form": search_form,
            "tasks": tasks,
            "all_tasks": all_tasks,
            "query_string": q,
            "can_create": self.can_create,
        }

    def get_create_tab_context_data(self):
        return {
            "create_form": self.create_form,
            "add_url": reverse("wagtailadmin_workflows:task_chooser_create")
            + "?"
            + self.request.GET.urlencode()
            if self.create_model
            else None,
            "task_types": self.get_task_type_options(),
        }


class TaskChooserView(BaseTaskChooserView):
    def get(self, request):
        self.create_form = self.get_create_form()
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = {
            "can_create": self.can_create,
        }
        context.update(self.get_task_listing_context_data())
        context.update(self.get_create_tab_context_data())
        return context

    def render_to_response(self, context):
        js_context = self.get_form_js_context()
        js_context["step"] = "chooser"

        return render_modal_workflow(
            self.request,
            "wagtailadmin/workflows/task_chooser/chooser.html",
            None,
            context,
            json_data=js_context,
        )


class TaskChooserCreateView(BaseTaskChooserView):
    def get(self, request):
        self.create_form = self.get_create_form()
        return super().get(request)

    def post(self, request):
        create_form_class = self.get_create_form_class()
        if not create_form_class:
            return HttpResponseBadRequest()

        self.create_form = create_form_class(
            request.POST, request.FILES, prefix="create-task"
        )

        if self.create_form.is_valid():
            task = self.create_form.save()
            return get_task_chosen_response(request, task)
        else:
            context = self.get_context_data()
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return self.get_create_tab_context_data()

    def render_to_response(self, context):
        tab_html = render_to_string(
            "wagtailadmin/workflows/task_chooser/includes/create_tab.html",
            context,
            self.request,
        )

        js_context = self.get_form_js_context()
        js_context["step"] = "reshow_create_tab"
        js_context["htmlFragment"] = tab_html

        return render_modal_workflow(
            self.request, None, None, None, json_data=js_context
        )


class TaskChooserResultsView(BaseTaskChooserView):
    template_name = "wagtailadmin/workflows/task_chooser/includes/results.html"

    def get_context_data(self, **kwargs):
        return self.get_task_listing_context_data()


def task_chosen(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return get_task_chosen_response(request, task)
