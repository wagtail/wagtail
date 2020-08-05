from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.filters import PageHistoryReportFilterSet
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.admin.views.reports import ReportView
from wagtail.core import hooks
from wagtail.core.models import (
    Page, PageLogEntry, PageRevision, Task, TaskState, UserPagePermissionsProxy, WorkflowState)

from wagtail.admin.views.pages.copy import *  # noqa
from wagtail.admin.views.pages.create import *  # noqa
from wagtail.admin.views.pages.edit import *  # noqa
from wagtail.admin.views.pages.listing import *  # noqa
from wagtail.admin.views.pages.lock import *  # noqa
from wagtail.admin.views.pages.moderation import *  # noqa
from wagtail.admin.views.pages.move import *  # noqa
from wagtail.admin.views.pages.preview import *  # noqa
from wagtail.admin.views.pages.search import *  # noqa
from wagtail.admin.views.pages.workflow import *  # noqa


def content_type_use(request, content_type_app_name, content_type_model_name):
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    page_class = content_type.model_class()

    # page_class must be a Page type and not some other random model
    if not issubclass(page_class, Page):
        raise Http404

    pages = page_class.objects.all()

    paginator = Paginator(pages, per_page=10)
    pages = paginator.get_page(request.GET.get('p'))

    return TemplateResponse(request, 'wagtailadmin/pages/content_type_use.html', {
        'pages': pages,
        'app_name': content_type_app_name,
        'content_type': content_type,
        'page_class': page_class,
    })


def delete(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_delete():
        raise PermissionDenied

    with transaction.atomic():
        for fn in hooks.get_hooks('before_delete_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        next_url = get_valid_next_url_from_request(request)

        if request.method == 'POST':
            parent_id = page.get_parent().id
            page.delete(user=request.user)

            messages.success(request, _("Page '{0}' deleted.").format(page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_delete_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if next_url:
                return redirect(next_url)
            return redirect('wagtailadmin_explore', parent_id)

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_delete.html', {
        'page': page,
        'descendant_count': page.get_descendant_count(),
        'next': next_url,
    })


def unpublish(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_unpublish():
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        include_descendants = request.POST.get("include_descendants", False)

        for fn in hooks.get_hooks('before_unpublish_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        page.unpublish(user=request.user)

        if include_descendants:
            live_descendant_pages = page.get_descendants().live().specific()
            for live_descendant_page in live_descendant_pages:
                if user_perms.for_page(live_descendant_page).can_unpublish():
                    live_descendant_page.unpublish()

        for fn in hooks.get_hooks('after_unpublish_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        messages.success(request, _("Page '{0}' unpublished.").format(page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_explore', page.get_parent().id)

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_unpublish.html', {
        'page': page,
        'next': next_url,
        'live_descendant_count': page.get_descendants().live().count(),
    })


def set_page_position(request, page_to_move_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    parent_page = page_to_move.get_parent()

    if not parent_page.permissions_for_user(request.user).can_reorder_children():
        raise PermissionDenied

    if request.method == 'POST':
        # Get position parameter
        position = request.GET.get('position', None)

        # Find page thats already in this position
        position_page = None
        if position is not None:
            try:
                position_page = parent_page.get_children()[int(position)]
            except IndexError:
                pass  # No page in this position

        # Move page

        # any invalid moves *should* be caught by the permission check above,
        # so don't bother to catch InvalidMoveToDescendant

        if position_page:
            # If the page has been moved to the right, insert it to the
            # right. If left, then left.
            old_position = list(parent_page.get_children()).index(page_to_move)
            if int(position) < old_position:
                page_to_move.move(position_page, pos='left')
            elif int(position) > old_position:
                page_to_move.move(position_page, pos='right')
        else:
            # Move page to end
            page_to_move.move(parent_page, pos='last-child')

    return HttpResponse('')


@require_GET
def preview_for_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.get_admin_display_title()))
        return redirect('wagtailadmin_home')

    page = revision.as_page_object()

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return page.make_preview_request(request, preview_mode, extra_request_attrs={
        'revision_id': revision_id
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


@user_passes_test(user_has_any_page_permission)
def revisions_index(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific

    # Get page ordering
    ordering = request.GET.get('ordering', '-created_at')
    if ordering not in ['created_at', '-created_at', ]:
        ordering = '-created_at'

    revisions = page.revisions.order_by(ordering)

    paginator = Paginator(revisions, per_page=20)
    revisions = paginator.get_page(request.GET.get('p'))

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/index.html', {
        'page': page,
        'ordering': ordering,
        'pagination_query_params': "ordering=%s" % ordering,
        'revisions': revisions,
    })


def revisions_revert(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_page_object()

    content_type = ContentType.objects.get_for_model(page)
    page_class = content_type.model_class()

    edit_handler = page_class.get_edit_handler()
    edit_handler = edit_handler.bind_to(instance=revision_page,
                                        request=request)
    form_class = edit_handler.get_form_class()

    form = form_class(instance=revision_page)
    edit_handler = edit_handler.bind_to(form=form)

    user_avatar = render_to_string('wagtailadmin/shared/user_avatar.html', {'user': revision.user})

    messages.warning(request, mark_safe(
        _("You are viewing a previous version of this page from <b>%(created_at)s</b> by %(user)s") % {
            'created_at': revision.created_at.strftime("%d %b %Y %H:%M"),
            'user': user_avatar,
        }
    ))

    return TemplateResponse(request, 'wagtailadmin/pages/edit.html', {
        'page': page,
        'revision': revision,
        'is_revision': True,
        'content_type': content_type,
        'edit_handler': edit_handler,
        'errors_debug': None,
        'action_menu': PageActionMenu(request, view='revisions_revert', page=page),
        'preview_modes': page.preview_modes,
        'form': form,  # Used in unit tests
    })


@user_passes_test(user_has_any_page_permission)
def revisions_view(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific

    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_page_object()

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return revision_page.make_preview_request(request, preview_mode)


def revisions_compare(request, page_id, revision_id_a, revision_id_b):
    page = get_object_or_404(Page, id=page_id).specific

    # Get revision to compare from
    if revision_id_a == 'live':
        if not page.live:
            raise Http404

        revision_a = page
        revision_a_heading = _("Live")
    elif revision_id_a == 'earliest':
        revision_a = page.revisions.order_by('created_at', 'id').first()
        if revision_a:
            revision_a = revision_a.as_page_object()
            revision_a_heading = _("Earliest")
        else:
            raise Http404
    else:
        revision_a = get_object_or_404(page.revisions, id=revision_id_a).as_page_object()
        revision_a_heading = str(get_object_or_404(page.revisions, id=revision_id_a).created_at)

    # Get revision to compare to
    if revision_id_b == 'live':
        if not page.live:
            raise Http404

        revision_b = page
        revision_b_heading = _("Live")
    elif revision_id_b == 'latest':
        revision_b = page.revisions.order_by('created_at', 'id').last()
        if revision_b:
            revision_b = revision_b.as_page_object()
            revision_b_heading = _("Latest")
        else:
            raise Http404
    else:
        revision_b = get_object_or_404(page.revisions, id=revision_id_b).as_page_object()
        revision_b_heading = str(get_object_or_404(page.revisions, id=revision_id_b).created_at)

    comparison = page.get_edit_handler().get_comparison()
    comparison = [comp(revision_a, revision_b) for comp in comparison]
    comparison = [comp for comp in comparison if comp.has_changed()]

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/compare.html', {
        'page': page,
        'revision_a_heading': revision_a_heading,
        'revision_a': revision_a,
        'revision_b_heading': revision_b_heading,
        'revision_b': revision_b,
        'comparison': comparison,
    })


def revisions_unschedule(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_unschedule():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)

    next_url = get_valid_next_url_from_request(request)

    subtitle = _('revision {0} of "{1}"').format(revision.id, page.get_admin_display_title())

    if request.method == 'POST':
        revision.approved_go_live_at = None
        revision.save(user=request.user, update_fields=['approved_go_live_at'])

        messages.success(request, _('Version {0} of "{1}" unscheduled.').format(revision.id, page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_pages:history', page.id)

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/confirm_unschedule.html', {
        'page': page,
        'revision': revision,
        'next': next_url,
        'subtitle': subtitle
    })


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
