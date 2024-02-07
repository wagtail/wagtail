import itertools
import re
from typing import Any, Mapping, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db.models import Exists, IntegerField, Max, OuterRef, Q
from django.db.models.functions import Cast
from django.forms import Media
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy
from django.views.generic.base import TemplateView

from wagtail import hooks
from wagtail.admin.navigation import get_site_for_user
from wagtail.admin.site_summary import SiteSummaryPanel
from wagtail.admin.ui.components import Component
from wagtail.admin.views.generic import WagtailAdminTemplateMixin
from wagtail.models import (
    Page,
    PageLogEntry,
    Revision,
    TaskState,
    WorkflowState,
    get_default_page_content_type,
)
from wagtail.permissions import page_permission_policy

User = get_user_model()


# Panels for the homepage


class UpgradeNotificationPanel(Component):
    name = "upgrade_notification"
    template_name = "wagtailadmin/home/upgrade_notification.html"
    order = 100

    def get_upgrade_check_setting(self) -> Union[bool, str]:
        return getattr(settings, "WAGTAIL_ENABLE_UPDATE_CHECK", True)

    def upgrade_check_lts_only(self) -> bool:
        upgrade_check = self.get_upgrade_check_setting()
        if isinstance(upgrade_check, str) and upgrade_check.lower() == "lts":
            return True
        return False

    def get_context_data(self, parent_context: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"lts_only": self.upgrade_check_lts_only()}

    def render_html(self, parent_context: Mapping[str, Any] = None) -> str:
        if (
            parent_context["request"].user.is_superuser
            and self.get_upgrade_check_setting()
        ):
            return super().render_html(parent_context)
        else:
            return ""


class WhatsNewInWagtailVersionPanel(Component):
    name = "whats_new_in_wagtail_version"
    template_name = "wagtailadmin/home/whats_new_in_wagtail_version.html"
    order = 110
    _version = "4"

    def get_whats_new_banner_setting(self) -> Union[bool, str]:
        return getattr(settings, "WAGTAIL_ENABLE_WHATS_NEW_BANNER", True)

    def get_dismissible_id(self) -> str:
        return f"{self.name}_{self._version}"

    def get_context_data(self, parent_context: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"dismissible_id": self.get_dismissible_id(), "version": self._version}

    def is_shown(self, parent_context: Mapping[str, Any] = None) -> bool:
        if not self.get_whats_new_banner_setting():
            return False

        profile = getattr(parent_context["request"].user, "wagtail_userprofile", None)
        if profile and profile.dismissibles.get(self.get_dismissible_id()):
            return False

        return True

    def render_html(self, parent_context: Mapping[str, Any] = None) -> str:
        if not self.is_shown(parent_context):
            return ""
        return super().render_html(parent_context)


class UserObjectsInWorkflowModerationPanel(Component):
    name = "user_objects_in_workflow_moderation"
    template_name = "wagtailadmin/home/user_objects_in_workflow_moderation.html"
    order = 210

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            # Need to cast the page ids to string because Postgres doesn't support
            # implicit type casts when querying on GenericRelations. We also need
            # to cast the object_id to integer when querying the pages for the same reason.
            # https://code.djangoproject.com/ticket/16055
            # Once the issue is resolved, this query can be removed and the
            # filter can be changed to:
            # Q(page__owner=request.user) | Q(requested_by=request.user)
            pages_owned_by_user = Q(
                base_content_type_id=get_default_page_content_type().id
            ) & Exists(
                Page.objects.filter(
                    owner=request.user,
                    id=Cast(OuterRef("object_id"), output_field=IntegerField()),
                )
            )
            # Find in progress workflow states which are either requested by the user or on pages owned by the user
            context["workflow_states"] = (
                WorkflowState.objects.active()
                .filter(pages_owned_by_user | Q(requested_by=request.user))
                .prefetch_related(
                    "content_object",
                    "content_object__latest_revision",
                )
                .select_related(
                    "current_task_state",
                    "current_task_state__task",
                )
                .order_by("-current_task_state__started_at")
            )
            # Filter out workflow states where the GenericForeignKey points to
            # a nonexistent object. This can happen if the model does not define
            # a GenericRelation to WorkflowState and the instance is deleted.
            context["workflow_states"] = [
                state for state in context["workflow_states"] if state.content_object
            ]
        else:
            context["workflow_states"] = WorkflowState.objects.none()
        context["request"] = request
        return context


class WorkflowObjectsToModeratePanel(Component):
    name = "workflow_objects_to_moderate"
    template_name = "wagtailadmin/home/workflow_objects_to_moderate.html"
    order = 220

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        context["states"] = []
        context["request"] = request
        context["csrf_token"] = parent_context["csrf_token"]

        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return context

        states = (
            TaskState.objects.reviewable_by(request.user)
            .select_related(
                "revision",
                "task",
                "revision__user",
                "workflow_state",
            )
            .prefetch_related(
                "revision__content_object",
                "revision__content_object__latest_revision",
                "revision__content_object__live_revision",
            )
            .order_by("-started_at")
        )
        for state in states:
            obj = state.revision.content_object
            # Skip task states where the revision's GenericForeignKey points to
            # a nonexistent object. This can happen if the model does not define
            # a GenericRelation to WorkflowState and/or Revision and the instance
            # is deleted.
            if not obj:
                continue
            actions = state.task.specific.get_actions(obj, request.user)
            workflow_tasks = state.workflow_state.all_tasks_with_status()

            workflow_action_url_name = "wagtailadmin_pages:workflow_action"
            workflow_preview_url_name = "wagtailadmin_pages:workflow_preview"
            revisions_compare_url_name = "wagtailadmin_pages:revisions_compare"

            # Snippets can also have workflows
            if not isinstance(obj, Page):
                viewset = obj.snippet_viewset
                workflow_action_url_name = viewset.get_url_name("workflow_action")
                workflow_preview_url_name = viewset.get_url_name("workflow_preview")
                revisions_compare_url_name = viewset.get_url_name("revisions_compare")

            if not getattr(obj, "is_previewable", False):
                workflow_preview_url_name = None

            try:
                previous_revision = state.revision.get_previous()
            except Revision.DoesNotExist:
                previous_revision = None

            context["states"].append(
                {
                    "obj": obj,
                    "revision": state.revision,
                    "previous_revision": previous_revision,
                    "live_revision": obj.live_revision,
                    "task_state": state,
                    "actions": actions,
                    "workflow_tasks": workflow_tasks,
                    "workflow_action_url_name": workflow_action_url_name,
                    "workflow_preview_url_name": workflow_preview_url_name,
                    "revisions_compare_url_name": revisions_compare_url_name,
                }
            )

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
                "can_remove_locks": page_permission_policy.user_has_permission(
                    request.user, "unlock"
                ),
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

        # Query the audit log to get a resultset of (page ID, latest edit timestamp)
        last_edits_dates = (
            PageLogEntry.objects.filter(user=request.user, action="wagtail.edit")
            .values("page_id")
            .annotate(latest_date=Max("timestamp"))
            .order_by("-latest_date")[:edit_count]
        )
        # Retrieve the page objects for those IDs
        pages_mapping = Page.objects.specific().in_bulk(
            [log["page_id"] for log in last_edits_dates]
        )
        # Compile a list of (latest edit timestamp, page object) tuples
        last_edits = []
        for log in last_edits_dates:
            page = pages_mapping.get(log["page_id"])
            if page:
                last_edits.append((log["latest_date"], page))

        context["last_edits"] = last_edits
        context["request"] = request
        return context


class HomeView(WagtailAdminTemplateMixin, TemplateView):
    template_name = "wagtailadmin/home.html"
    page_title = gettext_lazy("Dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panels = self.get_panels()
        site_details = self.get_site_details()

        context["media"] = self.get_media(panels)
        context["panels"] = sorted(panels, key=lambda p: p.order)
        context["user"] = self.request.user

        return {**context, **site_details}

    def get_media(self, panels=[]):
        media = Media()

        for panel in panels:
            media += panel.media

        return media

    def get_panels(self):
        request = self.request
        panels = [
            SiteSummaryPanel(request),
            # Disabled until a release warrants the banner.
            # WhatsNewInWagtailVersionPanel(),
            UpgradeNotificationPanel(),
            WorkflowObjectsToModeratePanel(),
            UserObjectsInWorkflowModerationPanel(),
            RecentEditsPanel(),
            LockedPagesPanel(),
        ]

        for fn in hooks.get_hooks("construct_homepage_panels"):
            fn(request, panels)

        return panels

    def get_site_details(self):
        request = self.request
        site = get_site_for_user(request.user)

        return {
            "root_page": site["root_page"],
            "root_site": site["root_site"],
            "site_name": site["site_name"],
        }


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


icon_comment_pattern = re.compile(r"<!--.*?-->")
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
            symbol = (
                render_to_string(icon)
                .replace('xmlns="http://www.w3.org/2000/svg"', "")
                .replace("svg", "symbol")
            )
            symbol = icon_comment_pattern.sub("", symbol)
            combined_icon_markup += symbol

        _icons_html = render_to_string(
            "wagtailadmin/shared/icons.html", {"icons": combined_icon_markup}
        )
    return _icons_html


def sprite(request):
    return HttpResponse(icons())
