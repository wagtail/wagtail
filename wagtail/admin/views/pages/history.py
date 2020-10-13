from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.filters import PageHistoryReportFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.core.models import (
    Page, PageLogEntry, PageRevision, TaskState, UserPagePermissionsProxy, WorkflowState)


def workflow_history(request, page_id):
    page = get_object_or_404(Page, id=page_id)

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_edit():
        raise PermissionDenied

    workflow_states = WorkflowState.objects.filter(page=page).order_by('-created_at')

    paginator = Paginator(workflow_states, per_page=20)
    workflow_states = paginator.get_page(request.GET.get('p'))

    return TemplateResponse(request, 'wagtailadmin/pages/workflow_history/index.html', {
        'page': page,
        'workflow_states': workflow_states,
    })


def workflow_history_detail(request, page_id, workflow_state_id):
    page = get_object_or_404(Page, id=page_id)

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_edit():
        raise PermissionDenied

    workflow_state = get_object_or_404(WorkflowState, page=page, id=workflow_state_id)

    # Get QuerySet of all revisions that have existed during this workflow state
    # It's possible that the page is edited while the workflow is running, so some
    # tasks may be repeated. All tasks that have been completed no matter what
    # revision needs to be displayed on this page.
    page_revisions = PageRevision.objects.filter(
        page=page,
        id__in=TaskState.objects.filter(workflow_state=workflow_state).values_list('page_revision_id', flat=True)
    ).order_by('-created_at')

    # Now get QuerySet of tasks completed for each revision
    task_states_by_revision_task = [
        (page_revision, {
            task_state.task: task_state
            for task_state in TaskState.objects.filter(workflow_state=workflow_state, page_revision=page_revision)
        })
        for page_revision in page_revisions
    ]

    # Make sure task states are always in a consistent order
    # In some cases, they can be completed in a different order to what they are defined
    tasks = workflow_state.workflow.tasks.all()
    task_states_by_revision = [
        (
            page_revision,
            [
                task_states_by_task.get(task, None)
                for task in tasks
            ]
        )
        for page_revision, task_states_by_task in task_states_by_revision_task
    ]

    # Generate timeline
    completed_task_states = TaskState.objects.filter(
        workflow_state=workflow_state
    ).exclude(
        finished_at__isnull=True
    ).exclude(
        status=TaskState.STATUS_CANCELLED
    )

    timeline = [
        {
            'time': workflow_state.created_at,
            'action': 'workflow_started',
            'workflow_state': workflow_state,
        }
    ]

    if workflow_state.status not in (WorkflowState.STATUS_IN_PROGRESS, WorkflowState.STATUS_NEEDS_CHANGES):
        last_task = completed_task_states.order_by('finished_at').last()
        if last_task:
            timeline.append({
                'time': last_task.finished_at + timedelta(milliseconds=1),
                'action': 'workflow_completed',
                'workflow_state': workflow_state,
            })

    for page_revision in page_revisions:
        timeline.append({
            'time': page_revision.created_at,
            'action': 'page_edited',
            'revision': page_revision,
        })

    for task_state in completed_task_states:
        timeline.append({
            'time': task_state.finished_at,
            'action': 'task_completed',
            'task_state': task_state,
        })

    timeline.sort(key=lambda t: t['time'])
    timeline.reverse()

    return TemplateResponse(request, 'wagtailadmin/pages/workflow_history/detail.html', {
        'page': page,
        'workflow_state': workflow_state,
        'tasks': tasks,
        'task_states_by_revision': task_states_by_revision,
        'timeline': timeline,
    })


class PageHistoryView(ReportView):
    template_name = 'wagtailadmin/pages/history.html'
    title = _('Page history')
    header_icon = 'history'
    paginate_by = 20
    filterset_class = PageHistoryReportFilterSet

    @method_decorator(user_passes_test(user_has_any_page_permission))
    def dispatch(self, request, *args, **kwargs):
        self.page = get_object_or_404(Page, id=kwargs.pop('page_id')).specific

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context['page'] = self.page
        context['subtitle'] = self.page.get_admin_display_title()

        return context

    def get_queryset(self):
        return PageLogEntry.objects.filter(page=self.page)
