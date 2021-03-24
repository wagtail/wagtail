import itertools

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db import connection
from django.db.models import Max, Q
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

from wagtail.admin.navigation import get_site_for_user
from wagtail.admin.site_summary import SiteSummaryPanel
from wagtail.core import hooks
from wagtail.core.models import (
    Page, PageRevision, TaskState, UserPagePermissionsProxy, WorkflowState)


User = get_user_model()


# Panels for the homepage

class UpgradeNotificationPanel:
    name = 'upgrade_notification'
    order = 100

    def __init__(self, request):
        self.request = request

    def render(self):
        if self.request.user.is_superuser and getattr(settings, "WAGTAIL_ENABLE_UPDATE_CHECK", True):
            return render_to_string('wagtailadmin/home/upgrade_notification.html', {}, request=self.request)
        else:
            return ""


class PagesForModerationPanel:
    name = 'pages_for_moderation'
    order = 200

    def __init__(self, request):
        self.request = request
        user_perms = UserPagePermissionsProxy(request.user)
        self.page_revisions_for_moderation = (user_perms.revisions_for_moderation()
                                              .select_related('page', 'user').order_by('-created_at'))

    def render(self):
        return render_to_string('wagtailadmin/home/pages_for_moderation.html', {
            'page_revisions_for_moderation': self.page_revisions_for_moderation,
        }, request=self.request)


class UserPagesInWorkflowModerationPanel:
    name = 'user_pages_in_workflow_moderation'
    order = 210

    def __init__(self, request):
        self.request = request
        # Find in progress workflow states which are either requested by the user or on pages owned by the user
        self.workflow_states = (
            WorkflowState.objects.active()
            .filter(Q(page__owner=request.user) | Q(requested_by=request.user))
            .select_related(
                'page', 'current_task_state', 'current_task_state__task', 'current_task_state__page_revision'
            )
            .order_by('-current_task_state__started_at')
        )

    def render(self):
        return render_to_string('wagtailadmin/home/user_pages_in_workflow_moderation.html', {
            'workflow_states': self.workflow_states
        }, request=self.request)


class WorkflowPagesToModeratePanel:
    name = 'workflow_pages_to_moderate'
    order = 220

    def __init__(self, request):
        self.request = request
        states = (
            TaskState.objects.reviewable_by(request.user)
            .select_related('page_revision', 'task', 'page_revision__page')
            .order_by('-started_at')
        )
        self.states = [
            (state, state.task.specific.get_actions(page=state.page_revision.page, user=request.user), state.workflow_state.all_tasks_with_status())
            for state in states
        ]

    def render(self):
        return render_to_string('wagtailadmin/home/workflow_pages_to_moderate.html', {
            'states': self.states
        }, request=self.request)


class LockedPagesPanel:
    name = 'locked_pages'
    order = 300

    def __init__(self, request):
        self.request = request

    def render(self):
        return render_to_string('wagtailadmin/home/locked_pages.html', {
            'locked_pages': Page.objects.filter(
                locked=True,
                locked_by=self.request.user,
            ),
            'can_remove_locks': UserPagePermissionsProxy(self.request.user).can_remove_locks()
        }, request=self.request)


class RecentEditsPanel:
    name = 'recent_edits'
    order = 250

    def __init__(self, request):
        self.request = request

        # Last n edited pages
        edit_count = getattr(settings, 'WAGTAILADMIN_RECENT_EDITS_LIMIT', 5)
        if connection.vendor == 'mysql':
            # MySQL can't handle the subselect created by the ORM version -
            # it fails with "This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'"
            last_edits = PageRevision.objects.raw(
                """
                SELECT wp.* FROM
                    wagtailcore_pagerevision wp JOIN (
                        SELECT max(created_at) AS max_created_at, page_id FROM
                            wagtailcore_pagerevision WHERE user_id = %s GROUP BY page_id ORDER BY max_created_at DESC LIMIT %s
                    ) AS max_rev ON max_rev.max_created_at = wp.created_at ORDER BY wp.created_at DESC
                 """, [
                    User._meta.pk.get_db_prep_value(self.request.user.pk, connection),
                    edit_count
                ]
            )
        else:
            last_edits_dates = (PageRevision.objects.filter(user=self.request.user)
                                .values('page_id').annotate(latest_date=Max('created_at'))
                                .order_by('-latest_date').values('latest_date')[:edit_count])
            last_edits = PageRevision.objects.filter(created_at__in=last_edits_dates).order_by('-created_at')

        page_keys = [pr.page_id for pr in last_edits]
        pages = Page.objects.specific().in_bulk(page_keys)
        self.last_edits = [
            [review, pages.get(review.page.pk)] for review in last_edits
        ]

    def render(self):
        return render_to_string('wagtailadmin/home/recent_edits.html', {
            'last_edits': list(self.last_edits),
        }, request=self.request)


def home(request):

    panels = [
        SiteSummaryPanel(request),
        UpgradeNotificationPanel(request),
        WorkflowPagesToModeratePanel(request),
        PagesForModerationPanel(request),
        UserPagesInWorkflowModerationPanel(request),
        RecentEditsPanel(request),
        LockedPagesPanel(request),
    ]

    for fn in hooks.get_hooks('construct_homepage_panels'):
        fn(request, panels)

    site_details = get_site_for_user(request.user)

    return TemplateResponse(request, "wagtailadmin/home.html", {
        'root_page': site_details['root_page'],
        'root_site': site_details['root_site'],
        'site_name': site_details['site_name'],
        'panels': sorted(panels, key=lambda p: p.order),
        'user': request.user
    })


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")


@permission_required('wagtailadmin.access_admin', login_url='wagtailadmin_login')
def default(request):
    """
    Called whenever a request comes in with the correct prefix (eg /admin/) but
    doesn't actually correspond to a Wagtail view.

    For authenticated users, it'll raise a 404 error. Anonymous users will be
    redirected to the login page.
    """
    raise Http404


_icons_html = None


def icons():
    global _icons_html
    if _icons_html is None:
        icon_hooks = hooks.get_hooks('register_icons')
        all_icons = sorted(itertools.chain.from_iterable(hook([]) for hook in icon_hooks))
        _icons_html = render_to_string("wagtailadmin/shared/icons.html", {'icons': all_icons})
    return _icons_html


def sprite(request):
    return HttpResponse(icons())
