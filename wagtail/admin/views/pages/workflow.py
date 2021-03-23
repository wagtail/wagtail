from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from django.views.generic import View

from wagtail.admin import messages
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core.models import Page, Task, TaskState, WorkflowState


class BaseWorkflowFormView(View):
    """
    Shared functionality for views that need to render the modal form to collect extra details
    for a workflow task
    """

    def dispatch(self, request, page_id, action_name, task_state_id):
        self.page = get_object_or_404(Page, id=page_id)
        self.action_name = action_name

        self.redirect_to = request.POST.get('next', None)
        if not self.redirect_to or not is_safe_url(url=self.redirect_to, allowed_hosts={request.get_host()}):
            self.redirect_to = reverse('wagtailadmin_pages:edit', args=[page_id])

        if not self.page.workflow_in_progress:
            messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(self.page.get_admin_display_title()))
            return redirect(self.redirect_to)

        self.task_state = get_object_or_404(TaskState, id=task_state_id)
        self.task_state = self.task_state.specific

        self.task = self.task_state.task.specific

        actions = self.task.get_actions(self.page, request.user)
        self.action_verbose_name = ''
        action_available = False
        self.action_modal = False

        for name, verbose_name, modal in actions:
            if name == self.action_name:
                action_available = True
                if modal:
                    self.action_modal = True
                    # if two actions have the same name, use the verbose name of the one allowing modal data entry
                    # within the modal
                    self.action_verbose_name = verbose_name
        if not action_available:
            raise PermissionDenied

        self.form_class = self.task.get_form_for_action(self.action_name)

        return super().dispatch(request, page_id, action_name, task_state_id)

    def post(self, request, page_id, action_name, task_state_id):
        raise NotImplementedError

    def get(self, request, page_id, action_name, task_state_id):
        form = self.form_class()
        return self.render_modal_form(request, form)

    def get_submit_url(self):
        raise NotImplementedError

    def render_modal_form(self, request, form):
        return render_modal_workflow(
            request, 'wagtailadmin/pages/workflow_action_modal.html', None, {
                'page': self.page,
                'form': form,
                'action': self.action_name,
                'action_verbose': self.action_verbose_name,
                'task_state': self.task_state,
                'submit_url': self.get_submit_url(),
            },
            json_data={'step': 'action'}
        )


class WorkflowAction(BaseWorkflowFormView):
    """Provides a modal view to enter additional data for the specified workflow action on GET,
    or perform the specified action on POST"""
    def post(self, request, page_id, action_name, task_state_id):
        if self.form_class:
            form = self.form_class(request.POST)
            if form.is_valid():
                redirect_to = self.task.on_action(self.task_state, request.user, self.action_name, **form.cleaned_data) or self.redirect_to
            elif self.action_modal and request.is_ajax():
                # show form errors
                return self.render_modal_form(request, form)
        else:
            redirect_to = self.task.on_action(self.task_state, request.user, self.action_name) or self.redirect_to

        if request.is_ajax():
            return render_modal_workflow(request, '', None, {}, json_data={'step': 'success', 'redirect': redirect_to})
        return redirect(redirect_to)

    def get_submit_url(self):
        return reverse('wagtailadmin_pages:workflow_action', args=(self.page.id, self.action_name, self.task_state.id))


class CollectWorkflowActionData(BaseWorkflowFormView):
    """
    On GET, provides a modal view to enter additional data for the specified workflow action;
    on POST, return the validated form data back to the modal's caller via a JSON response, so that
    the calling view can subsequently perform the action as part of its own processing
    (for example, approving moderation while making an edit).
    """
    def post(self, request, page_id, action_name, task_state_id):
        form = self.form_class(request.POST)
        if form.is_valid():
            return render_modal_workflow(request, '', None, {}, json_data={'step': 'success', 'cleaned_data': form.cleaned_data})
        elif self.action_modal and request.is_ajax():
            # show form errors
            return self.render_modal_form(request, form)

    def get_submit_url(self):
        return reverse('wagtailadmin_pages:collect_workflow_action_data', args=(self.page.id, self.action_name, self.task_state.id))


def confirm_workflow_cancellation(request, page_id):
    """Provides a modal view to confirm that the user wants to publish the page even though it will cancel the current workflow"""
    page = get_object_or_404(Page, id=page_id)
    workflow_state = page.current_workflow_state

    if (not workflow_state) or not getattr(settings, 'WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH', True):
        return render_modal_workflow(request, '', None, {}, json_data={'step': 'no_confirmation_needed'})

    return render_modal_workflow(
        request, 'wagtailadmin/pages/confirm_workflow_cancellation.html', None, {
            'needs_changes': workflow_state.status == WorkflowState.STATUS_NEEDS_CHANGES,
            'task': workflow_state.current_task_state.task.name,
            'workflow': workflow_state.workflow.name,
        },
        json_data={'step': 'confirm'}
    )


@require_GET
@user_passes_test(user_has_any_page_permission)
def workflow_status(request, page_id):
    page = get_object_or_404(Page, id=page_id)
    current_workflow_state = page.current_workflow_state
    if not current_workflow_state:
        raise PermissionDenied

    workflow_tasks = []
    workflow_state = current_workflow_state
    if not workflow_state:
        # Show last workflow state
        workflow_state = page.workflow_states.order_by('created_at').last()

    if workflow_state:
        workflow_tasks = workflow_state.all_tasks_with_state()

    return render_modal_workflow(request, 'wagtailadmin/workflows/workflow_status.html', None, {
        'page': page,
        'workflow_state': workflow_state,
        'current_task_state': workflow_state.current_task_state if workflow_state else None,
        'workflow_tasks': workflow_tasks,
    })


@require_GET
def preview_revision_for_task(request, page_id, task_id):
    """Preview the revision linked to the in-progress TaskState of a specified Task. This enables pages in moderation
    to be edited and new TaskStates linked to the new revisions created, with preview links remaining valid"""

    page = get_object_or_404(Page, id=page_id)
    task = get_object_or_404(Task, id=task_id).specific
    try:
        task_state = TaskState.objects.get(page_revision__page=page, task=task, status=TaskState.STATUS_IN_PROGRESS)
    except TaskState.DoesNotExist:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation in task '{1}'.").format(page.get_admin_display_title(), task.name))
        return redirect('wagtailadmin_home')

    revision = task_state.page_revision

    if not task.get_actions(page, request.user):
        raise PermissionDenied

    page_to_view = revision.as_page_object()

    # TODO: provide workflow actions within this view

    return page_to_view.make_preview_request(request, page.default_preview_mode, extra_request_attrs={
        'revision_id': revision.id
    })
