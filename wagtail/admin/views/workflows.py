from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.functions import Lower
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.workflows import (
    TaskChooserSearchForm, WorkflowPagesFormSet, get_task_form_class, get_workflow_edit_handler)
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.core.models import (
    Page, Task, TaskState, UserPagePermissionsProxy, Workflow, WorkflowState)
from wagtail.core.permissions import task_permission_policy, workflow_permission_policy
from wagtail.core.utils import resolve_model_string
from wagtail.core.workflows import get_task_types


task_permission_checker = PermissionPolicyChecker(task_permission_policy)


class Index(IndexView):
    permission_policy = workflow_permission_policy
    model = Workflow
    context_object_name = 'workflows'
    template_name = 'wagtailadmin/workflows/index.html'
    add_url_name = 'wagtailadmin_workflows:add'
    edit_url_name = 'wagtailadmin_workflows:edit'
    page_title = _("Workflows")
    add_item_label = _("Add a workflow")
    header_icon = 'tasks'

    def show_disabled(self):
        return self.request.GET.get('show_disabled', 'false') == 'true'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.show_disabled():
            queryset = queryset.filter(active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['showing_disabled'] = self.show_disabled()
        return context


class Create(CreateView):
    permission_policy = workflow_permission_policy
    model = Workflow
    page_title = _("New workflow")
    template_name = 'wagtailadmin/workflows/create.html'
    success_message = _("Workflow '{0}' created.")
    add_url_name = 'wagtailadmin_workflows:add'
    edit_url_name = 'wagtailadmin_workflows:edit'
    index_url_name = 'wagtailadmin_workflows:index'
    header_icon = 'tasks'
    edit_handler = None

    def get_edit_handler(self):
        if not self.edit_handler:
            self.edit_handler = get_workflow_edit_handler().bind_to(request=self.request)
        return self.edit_handler

    def get_form_class(self):
        return self.get_edit_handler().get_form_class()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        self.edit_handler = self.edit_handler.bind_to(form=form)
        return form

    def get_pages_formset(self):
        if self.request.method == 'POST':
            return WorkflowPagesFormSet(self.request.POST, instance=self.object, prefix='pages')
        else:
            return WorkflowPagesFormSet(instance=self.object, prefix='pages')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edit_handler'] = self.edit_handler
        context['pages_formset'] = self.get_pages_formset()
        return context

    def form_valid(self, form):
        self.form = form

        with transaction.atomic():
            self.object = self.save_instance()

            pages_formset = self.get_pages_formset()
            if pages_formset.is_valid():
                pages_formset.save()

                success_message = self.get_success_message(self.object)
                if success_message is not None:
                    messages.success(self.request, success_message, buttons=[
                        messages.button(reverse(self.edit_url_name, args=(self.object.id,)), _('Edit'))
                    ])
                return redirect(self.get_success_url())

            else:
                transaction.set_rollback(True)

        return self.form_invalid(form)


class Edit(EditView):
    permission_policy = workflow_permission_policy
    model = Workflow
    page_title = _("Editing workflow")
    template_name = 'wagtailadmin/workflows/edit.html'
    success_message = _("Workflow '{0}' updated.")
    add_url_name = 'wagtailadmin_workflows:add'
    edit_url_name = 'wagtailadmin_workflows:edit'
    delete_url_name = 'wagtailadmin_workflows:disable'
    delete_item_label = _('Disable')
    index_url_name = 'wagtailadmin_workflows:index'
    enable_item_label = _('Enable')
    enable_url_name = 'wagtailadmin_workflows:enable'
    header_icon = 'tasks'
    edit_handler = None
    MAX_PAGES = 5

    def get_edit_handler(self):
        if not self.edit_handler:
            self.edit_handler = get_workflow_edit_handler().bind_to(request=self.request)
        return self.edit_handler

    def get_form_class(self):
        return self.get_edit_handler().get_form_class()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        self.edit_handler = self.edit_handler.bind_to(form=form)
        return form

    def get_pages_formset(self):
        if self.request.method == 'POST':
            return WorkflowPagesFormSet(self.request.POST, instance=self.get_object(), prefix='pages')
        else:
            return WorkflowPagesFormSet(instance=self.get_object(), prefix='pages')

    def get_paginated_pages(self):
        # Get the (paginated) list of Pages to which this Workflow is assigned.
        pages = Page.objects.filter(workflowpage__workflow=self.get_object())
        pages.paginator = Paginator(pages, self.MAX_PAGES)
        page_number = int(self.request.GET.get('p', 1))
        paginated_pages = pages.paginator.page(page_number)
        return paginated_pages

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edit_handler'] = self.edit_handler
        context['pages'] = self.get_paginated_pages()
        context['pages_formset'] = self.get_pages_formset()
        context['can_disable'] = (self.permission_policy is None or self.permission_policy.user_has_permission(self.request.user, 'delete')) and self.object.active
        context['can_enable'] = (self.permission_policy is None or self.permission_policy.user_has_permission(
            self.request.user, 'create')) and not self.object.active
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

            # Save pages formset
            # Note: The pages formset is hidden when the page is inactive
            if self.object.active:
                pages_formset = self.get_pages_formset()
                if pages_formset.is_valid():
                    pages_formset.save()
                else:
                    transaction.set_rollback(True)
                    successful = False

            if successful:
                success_message = self.get_success_message()
                if success_message is not None:
                    messages.success(self.request, success_message, buttons=[
                        messages.button(reverse(self.edit_url_name, args=(self.object.id,)), _('Edit'))
                    ])
                return redirect(self.get_success_url())

        return self.form_invalid(form)


class Disable(DeleteView):
    permission_policy = workflow_permission_policy
    model = Workflow
    page_title = _("Disable workflow")
    template_name = 'wagtailadmin/workflows/confirm_disable.html'
    success_message = _("Workflow '{0}' disabled.")
    add_url_name = 'wagtailadmin_workflows:add'
    edit_url_name = 'wagtailadmin_workflows:edit'
    delete_url_name = 'wagtailadmin_workflows:disable'
    index_url_name = 'wagtailadmin_workflows:index'
    header_icon = 'tasks'

    @property
    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.kwargs['pk'],))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        states_in_progress = WorkflowState.objects.filter(status=WorkflowState.STATUS_IN_PROGRESS).count()
        context['warning_message'] = ngettext(
            'This workflow is in progress on %(states_in_progress)d page. Disabling this workflow will cancel moderation on this page.',
            'This workflow is in progress on %(states_in_progress)d pages. Disabling this workflow will cancel moderation on these pages.',
            states_in_progress,
        ) % {
            'states_in_progress': states_in_progress,
        }
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deactivate(user=request.user)
        messages.success(request, self.get_success_message())
        return redirect(reverse(self.index_url_name))


def usage(request, pk):
    workflow = get_object_or_404(Workflow, id=pk)

    perms = UserPagePermissionsProxy(request.user)

    pages = workflow.all_pages() & perms.editable_pages()
    paginator = Paginator(pages, per_page=10)
    pages = paginator.get_page(request.GET.get('p'))

    return render(request, 'wagtailadmin/workflows/usage.html', {
        'workflow': workflow,
        'used_by': pages,
    })


@require_POST
def enable_workflow(request, pk):
    # Reactivate an inactive workflow
    workflow = get_object_or_404(Workflow, id=pk)

    # Check permissions
    if not workflow_permission_policy.user_has_permission(request.user, 'create'):
        raise PermissionDenied

    # Set workflow to active if inactive
    if not workflow.active:
        workflow.active = True
        workflow.save()
        messages.success(request, _("Workflow '{0}' enabled.").format(workflow.name))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_workflows:edit', workflow.id)


@require_POST
def remove_workflow(request, page_pk, workflow_pk=None):
    # Remove a workflow from a page (specifically a single workflow if workflow_pk is set)
    # Get the page
    page = get_object_or_404(Page, id=page_pk)

    # Check permissions
    if not workflow_permission_policy.user_has_permission(request.user, 'change'):
        raise PermissionDenied

    if hasattr(page, 'workflowpage'):
        # If workflow_pk is set, this will only remove the workflow if it its pk matches - this prevents accidental
        # removal of the wrong workflow via a workflow edit page if the page listing is out of date
        if not workflow_pk or workflow_pk == page.workflowpage.workflow.pk:
            page.workflowpage.delete()
            messages.success(request, _("Workflow removed from Page '{0}'.").format(page.get_admin_display_title()))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.id)


class TaskIndex(IndexView):
    permission_policy = task_permission_policy
    model = Task
    context_object_name = 'tasks'
    template_name = 'wagtailadmin/workflows/task_index.html'
    add_url_name = 'wagtailadmin_workflows:select_task_type'
    edit_url_name = 'wagtailadmin_workflows:edit_task'
    page_title = _("Workflow tasks")
    add_item_label = _("New workflow task")
    header_icon = 'thumbtack'

    def show_disabled(self):
        return self.request.GET.get('show_disabled', 'false') == 'true'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.show_disabled():
            queryset = queryset.filter(active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['showing_disabled'] = self.show_disabled()
        return context


def select_task_type(request):
    if not task_permission_policy.user_has_permission(request.user, 'add'):
        raise PermissionDenied

    task_types = [
        (model.get_verbose_name(), model._meta.app_label, model._meta.model_name, model.get_description())
        for model in get_task_types()
    ]
    # sort by lower-cased version of verbose name
    task_types.sort(key=lambda task_type: task_type[0].lower())

    if len(task_types) == 1:
        # Only one task type is available - redirect straight to the create form rather than
        # making the user choose
        verbose_name, app_label, model_name, description = task_types[0]
        return redirect('wagtailadmin_workflows:add_task', app_label, model_name)

    return render(request, 'wagtailadmin/workflows/select_task_type.html', {
        'task_types': task_types,
        'icon': 'thumbtack',
        'title': _("Workflows"),
    })


class CreateTask(CreateView):
    permission_policy = task_permission_policy
    model = None
    page_title = _("New workflow task")
    template_name = 'wagtailadmin/workflows/create_task.html'
    success_message = _("Task '{0}' created.")
    add_url_name = 'wagtailadmin_workflows:add_task'
    edit_url_name = 'wagtailadmin_workflows:edit_task'
    index_url_name = 'wagtailadmin_workflows:task_index'
    header_icon = 'thumbtack'

    @cached_property
    def model(self):
        try:
            content_type = ContentType.objects.get_by_natural_key(self.kwargs['app_label'], self.kwargs['model_name'])
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
        return reverse(self.add_url_name, kwargs={'app_label': self.kwargs.get('app_label'), 'model_name': self.kwargs.get('model_name')})


class EditTask(EditView):
    permission_policy = task_permission_policy
    model = None
    page_title = _("Editing workflow task")
    template_name = 'wagtailadmin/workflows/edit_task.html'
    success_message = _("Task '{0}' updated.")
    add_url_name = 'wagtailadmin_workflows:select_task_type'
    edit_url_name = 'wagtailadmin_workflows:edit_task'
    delete_url_name = 'wagtailadmin_workflows:disable_task'
    index_url_name = 'wagtailadmin_workflows:task_index'
    delete_item_label = _('Disable')
    enable_item_label = _('Enable')
    enable_url_name = 'wagtailadmin_workflows:enable_task'
    header_icon = 'thumbtack'

    @cached_property
    def model(self):
        return type(self.get_object())

    @cached_property
    def page_title(self):
        return _("Editing %(task_type)s") % {'task_type': self.get_object().content_type.name}

    def get_queryset(self):
        if self.queryset is None:
            return Task.objects.all()

    def get_object(self, queryset=None):
        return super().get_object().specific

    def get_form_class(self):
        return get_task_form_class(self.model, for_edit=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_disable'] = (self.permission_policy is None or self.permission_policy.user_has_permission(self.request.user, 'delete')) and self.object.active
        context['can_enable'] = (self.permission_policy is None or self.permission_policy.user_has_permission(self.request.user, 'create')) and not self.object.active

        # TODO: add warning msg when there are pages currently on this task in a workflow, add interaction like resetting task state when saved
        return context

    @property
    def get_enable_url(self):
        return reverse(self.enable_url_name, args=(self.object.pk,))


class DisableTask(DeleteView):
    permission_policy = task_permission_policy
    model = Task
    page_title = _("Disable task")
    template_name = 'wagtailadmin/workflows/confirm_disable_task.html'
    success_message = _("Task '{0}' disabled.")
    add_url_name = 'wagtailadmin_workflows:add_task'
    edit_url_name = 'wagtailadmin_workflows:edit_task'
    delete_url_name = 'wagtailadmin_workflows:disable_task'
    index_url_name = 'wagtailadmin_workflows:task_index'
    header_icon = 'thumbtack'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        states_in_progress = TaskState.objects.filter(status=TaskState.STATUS_IN_PROGRESS).count()
        context['warning_message'] = ngettext(
            'This task is in progress on %(states_in_progress)d page. Disabling this task will cause it to be skipped in the moderation workflow.',
            'This task is in progress on %(states_in_progress)d pages. Disabling this task will cause it to be skipped in the moderation workflow.',
            states_in_progress,
        ) % {
            'states_in_progress': states_in_progress,
        }
        return context

    @property
    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.kwargs['pk'],))

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deactivate(user=request.user)
        messages.success(request, self.get_success_message())
        return redirect(reverse(self.index_url_name))


@require_POST
def enable_task(request, pk):
    # Reactivate an inactive task
    task = get_object_or_404(Task, id=pk)

    # Check permissions
    if not task_permission_policy.user_has_permission(request.user, 'create'):
        raise PermissionDenied

    # Set workflow to active if inactive
    if not task.active:
        task.active = True
        task.save()
        messages.success(request, _("Task '{0}' enabled.").format(task.name))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_workflows:edit_task', task.id)


def get_chooser_context():
    """construct context variables needed by the chooser JS"""
    return {
        'step': 'chooser',
        'error_label': _("Server Error"),
        'error_message': _("Report this error to your webmaster with the following information:"),
    }


def get_task_result_data(task):
    """
    helper function: given a task, return the json data to pass back to the
    chooser panel
    """

    return {
        'id': task.id,
        'name': task.name,
        'edit_url': reverse('wagtailadmin_workflows:edit_task', args=[task.id]),
    }


def task_chooser(request):
    task_models = get_task_types()
    create_model = None
    can_create = False

    if task_permission_policy.user_has_permission(request.user, 'add'):
        can_create = len(task_models) != 0

        if len(task_models) == 1:
            create_model = task_models[0]

        elif 'create_model' in request.GET:
            create_model = resolve_model_string(request.GET['create_model'])

            if create_model not in task_models:
                raise Http404

    # Build task types list for "select task type" view
    task_types = [
        (model.get_verbose_name(), model._meta.app_label, model._meta.model_name, model.get_description())
        for model in task_models
    ]
    # sort by lower-cased version of verbose name
    task_types.sort(key=lambda task_type: task_type[0].lower())

    # Build task type choices for filter on "existing task" tab
    task_type_choices = [
        (model, model.get_verbose_name())
        for model in task_models
    ]
    task_type_choices.sort(key=lambda task_type: task_type[1].lower())

    if create_model:
        createform_class = get_task_form_class(create_model)
    else:
        createform_class = None

    q = None
    if 'q' in request.GET or 'p' in request.GET or 'task_type' in request.GET:
        searchform = TaskChooserSearchForm(request.GET, task_type_choices=task_type_choices)
        tasks = all_tasks = searchform.task_model.objects.order_by(Lower('name'))
        q = ''

        if searchform.is_searching():
            # Note: I decided not to use wagtailsearch here. This is because
            # wagtailsearch creates a new index for each model you make
            # searchable and this might affect someone's quota. I doubt there
            # would ever be enough tasks to require using anything more than
            # an icontains anyway.
            q = searchform.cleaned_data['q']
            tasks = tasks.filter(name__icontains=q)

        # Pagination
        paginator = Paginator(tasks, per_page=10)
        tasks = paginator.get_page(request.GET.get('p'))

        return TemplateResponse(request, "wagtailadmin/workflows/task_chooser/includes/results.html", {
            'task_types': task_types,
            'searchform': searchform,
            'tasks': tasks,
            'all_tasks': all_tasks,
            'query_string': q,
        })
    else:
        if createform_class:
            if request.method == 'POST':
                createform = createform_class(request.POST, request.FILES, prefix='create-task')

                if createform.is_valid():
                    task = createform.save()

                    response = render_modal_workflow(
                        request, None, None,
                        None, json_data={'step': 'task_chosen', 'result': get_task_result_data(task)}
                    )

                    # Use a different status code so we can tell the difference between validation errors and successful creations
                    response.status_code = 201

                    return response
            else:
                createform = createform_class(prefix='create-task')
        else:
            if request.method == 'POST':
                return HttpResponseBadRequest()

            createform = None

        searchform = TaskChooserSearchForm(task_type_choices=task_type_choices)
        tasks = searchform.task_model.objects.order_by(Lower('name'))

        paginator = Paginator(tasks, per_page=10)
        tasks = paginator.get_page(request.GET.get('p'))

        return render_modal_workflow(request, 'wagtailadmin/workflows/task_chooser/chooser.html', None, {
            'task_types': task_types,
            'tasks': tasks,
            'searchform': searchform,
            'createform': createform,
            'can_create': can_create,
            'add_url': reverse('wagtailadmin_workflows:task_chooser') + '?' + request.GET.urlencode() if create_model else None
        }, json_data=get_chooser_context())


def task_chosen(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    return render_modal_workflow(
        request, None, None,
        None, json_data={'step': 'task_chosen', 'result': get_task_result_data(task)}
    )
