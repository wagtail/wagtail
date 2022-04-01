import itertools

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db import connection
from django.db.models import Max, Q
from django.forms import Media
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

from wagtail import hooks
from wagtail.admin.navigation import get_site_for_user
from wagtail.admin.site_summary import SiteSummaryPanel
from wagtail.admin.ui.components import Component
from wagtail.models import (
    Page,
    PageRevision,
    TaskState,
    UserPagePermissionsProxy,
    WorkflowState,
)

User = get_user_model()


# Panels for the homepage


class UpgradeNotificationPanel(Component):
    name = "upgrade_notification"
    template_name = "wagtailadmin/home/upgrade_notification.html"
    order = 100

    def render_html(self, parent_context):
        if parent_context["request"].user.is_superuser and getattr(
            settings, "WAGTAIL_ENABLE_UPDATE_CHECK", True
        ):
            return super().render_html(parent_context)
        else:
            return ""


class PagesForModerationPanel(Component):
    name = "pages_for_moderation"
    template_name = "wagtailadmin/home/pages_for_moderation.html"
    order = 200

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        user_perms = UserPagePermissionsProxy(request.user)
        context["page_revisions_for_moderation"] = (
            user_perms.revisions_for_moderation()
            .select_related("page", "user")
            .order_by("-created_at")
        )
        context["request"] = request
        context["csrf_token"] = parent_context["csrf_token"]
        return context


class UserPagesInWorkflowModerationPanel(Component):
    name = "user_pages_in_workflow_moderation"
    template_name = "wagtailadmin/home/user_pages_in_workflow_moderation.html"
    order = 210

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            # Find in progress workflow states which are either requested by the user or on pages owned by the user
            context["workflow_states"] = (
                WorkflowState.objects.active()
                .filter(Q(page__owner=request.user) | Q(requested_by=request.user))
                .select_related(
                    "page",
                    "current_task_state",
                    "current_task_state__task",
                    "current_task_state__page_revision",
                )
                .order_by("-current_task_state__started_at")
            )
        else:
            context["workflow_states"] = WorkflowState.objects.none()
        context["request"] = request
        return context


class WorkflowPagesToModeratePanel(Component):
    name = "workflow_pages_to_moderate"
    template_name = "wagtailadmin/home/workflow_pages_to_moderate.html"
    order = 220

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            states = (
                TaskState.objects.reviewable_by(request.user)
                .select_related(
                    "page_revision",
                    "task",
                    "page_revision__page",
                    "page_revision__user",
                )
                .order_by("-started_at")
            )
            context["states"] = [
                (
                    state,
                    state.task.specific.get_actions(
                        page=state.page_revision.page, user=request.user
                    ),
                    state.workflow_state.all_tasks_with_status(),
                )
                for state in states
            ]
        else:
            context["states"] = []
        context["request"] = request
        context["csrf_token"] = parent_context["csrf_token"]
        return context


class LockedPagesPanel(Component):
    name = "locked_pages"
    template_name = "wagtailadmin/home/locked_pages.html"
    order = 300

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        context.update(
            {
                "locked_pages": Page.objects.filter(
                    locked=True,
                    locked_by=request.user,
                ),
                "can_remove_locks": UserPagePermissionsProxy(
                    request.user
                ).can_remove_locks(),
                "request": request,
                "csrf_token": parent_context["csrf_token"],
            }
        )
        return context


class RecentEditsPanel(Component):
    name = "recent_edits"
    template_name = "wagtailadmin/home/recent_edits.html"
    order = 250

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)

        # Last n edited pages
        edit_count = getattr(settings, "WAGTAILADMIN_RECENT_EDITS_LIMIT", 5)
        if connection.vendor == "mysql":
            # MySQL can't handle the subselect created by the ORM version -
            # it fails with "This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'"
            last_edits = PageRevision.objects.raw(
                """
                SELECT wp.* FROM
                    wagtailcore_pagerevision wp JOIN (
                        SELECT max(created_at) AS max_created_at, page_id FROM
                            wagtailcore_pagerevision WHERE user_id = %s GROUP BY page_id ORDER BY max_created_at DESC LIMIT %s
                    ) AS max_rev ON max_rev.max_created_at = wp.created_at ORDER BY wp.created_at DESC
                 """,
                [
                    User._meta.pk.get_db_prep_value(request.user.pk, connection),
                    edit_count,
                ],
            )
        else:
            last_edits_dates = (
                PageRevision.objects.filter(user=request.user)
                .values("page_id")
                .annotate(latest_date=Max("created_at"))
                .order_by("-latest_date")
                .values("latest_date")[:edit_count]
            )
            last_edits = PageRevision.objects.filter(
                created_at__in=last_edits_dates
            ).order_by("-created_at")

        page_keys = [pr.page_id for pr in last_edits]
        pages = Page.objects.specific().in_bulk(page_keys)
        context["last_edits"] = [
            [revision, pages.get(revision.page_id)] for revision in last_edits
        ]
        context["request"] = request
        return context


def home(request):

    panels = [
        SiteSummaryPanel(request),
        UpgradeNotificationPanel(),
        WorkflowPagesToModeratePanel(),
        PagesForModerationPanel(),
        UserPagesInWorkflowModerationPanel(),
        RecentEditsPanel(),
        LockedPagesPanel(),
    ]

    for fn in hooks.get_hooks("construct_homepage_panels"):
        fn(request, panels)

    media = Media()

    for panel in panels:
        media += panel.media

    site_details = get_site_for_user(request.user)

    return TemplateResponse(
        request,
        "wagtailadmin/home.html",
        {
            "root_page": site_details["root_page"],
            "root_site": site_details["root_site"],
            "site_name": site_details["site_name"],
            "panels": sorted(panels, key=lambda p: p.order),
            "user": request.user,
            "media": media,
        },
    )


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")


@permission_required("wagtailadmin.access_admin", login_url="wagtailadmin_login")
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
        icon_hooks = hooks.get_hooks("register_icons")
        all_icons = sorted(
            itertools.chain.from_iterable(hook([]) for hook in icon_hooks)
        )
        combined_icon_markup = ""
        for icon in all_icons:
            combined_icon_markup += render_to_string(icon).replace("svg", "symbol")

        _full_sprite_html = render_to_string(
            "wagtailadmin/shared/icons.html", {"icons": combined_icon_markup}
        )
    return _full_sprite_html


def sprite(request):
    return HttpResponse(icons())
