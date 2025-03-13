import warnings

from django.conf import settings
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy, ngettext

from wagtail.admin.ui.components import Component
from wagtail.admin.userbar import AccessibilityItem, apply_userbar_hooks
from wagtail.models import DraftStateMixin, LockableMixin, Page, ReferenceIndex
from wagtail.utils.deprecation import RemovedInWagtail70Warning


class BaseSidePanel(Component):
    class SidePanelToggle(Component):
        template_name = "wagtailadmin/shared/side_panel_toggle.html"
        aria_label = ""
        icon_name = ""
        has_counter = True
        counter_classname = ""
        keyboard_shortcut = None

        def __init__(self, panel):
            self.panel = panel

        def get_context_data(self, parent_context):
            # Inherit classes from fragments defined in slim_header.html
            inherit = {
                "nav_icon_button_classes",
                "nav_icon_classes",
                "nav_icon_counter_classes",
            }
            context = {key: parent_context.get(key) for key in inherit}
            context["toggle"] = self
            context["panel"] = self.panel
            context["count"] = 0
            return context

    def __init__(self, object, request):
        self.object = object
        self.request = request
        self.model = type(self.object)
        self.toggle = self.SidePanelToggle(panel=self)

    def get_context_data(self, parent_context):
        context = {"panel": self, "object": self.object, "request": self.request}
        if issubclass(self.model, Page):
            context["page"] = self.object
        return context


class StatusSidePanel(BaseSidePanel):
    class SidePanelToggle(BaseSidePanel.SidePanelToggle):
        aria_label = gettext_lazy("Toggle status")
        icon_name = "info-circle"
        counter_classname = "w-bg-critical-200"

        def get_context_data(self, parent_context):
            context = super().get_context_data(parent_context)
            form = parent_context.get("form")
            context["count"] = form and len(
                form.errors.keys() & {"go_live_at", "expire_at"}
            )
            return context

    name = "status"
    title = gettext_lazy("Status")
    template_name = "wagtailadmin/shared/side_panels/status.html"
    order = 100

    def __init__(
        self,
        *args,
        show_schedule_publishing_toggle=None,
        live_object=None,
        scheduled_object=None,
        locale=None,
        translations=None,
        usage_url=None,
        history_url=None,
        last_updated_info=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.show_schedule_publishing_toggle = show_schedule_publishing_toggle
        self.live_object = live_object
        self.scheduled_object = scheduled_object
        self.locale = locale
        self.translations = translations
        self.usage_url = usage_url
        self.history_url = history_url
        self.last_updated_info = last_updated_info
        self.locking_enabled = isinstance(self.object, LockableMixin)

    def get_status_templates(self, context):
        templates = ["wagtailadmin/shared/side_panels/includes/status/workflow.html"]

        if self.locale:
            templates.append(
                "wagtailadmin/shared/side_panels/includes/status/locale.html"
            )

        if self.object.pk:
            if self.locking_enabled:
                templates.append(
                    "wagtailadmin/shared/side_panels/includes/status/locked.html"
                )

            if self.usage_url:
                templates.append(
                    "wagtailadmin/shared/side_panels/includes/status/usage.html"
                )

        return templates

    def get_scheduled_publishing_context(self, parent_context):
        if not isinstance(self.object, DraftStateMixin):
            return {"draftstate_enabled": False}

        context = {
            # Used for hiding the info completely if the model doesn't extend DraftStateMixin
            "draftstate_enabled": True,
            # Show error message if any of the scheduled publishing fields has errors
            "schedule_has_errors": False,
            # The dialog toggle can be hidden (e.g. if PublishingPanel is not present)
            # but the scheduled publishing info should still be shown
            "show_schedule_publishing_toggle": self.show_schedule_publishing_toggle,
            # These are the dates that show up with the unticked calendar icon,
            # aka "draft schedule"
            "draft_go_live_at": None,
            "draft_expire_at": None,
            # These are the dates that show up with the ticked calendar icon,
            # aka "active schedule"
            "scheduled_go_live_at": None,
            "scheduled_expire_at": None,
            # This is for an edge case where the live object already has an
            # expire_at, which can still take effect if the active schedule's
            # go_live_at is later than that
            "live_expire_at": None,
        }

        # Reuse logic from the toggle to get the count of errors
        if self.toggle.get_context_data(parent_context)["count"]:
            context["schedule_has_errors"] = True

        # Only consider draft schedule if the object hasn't been created
        # or if there are unpublished changes
        if not self.object.pk or self.object.has_unpublished_changes:
            context["draft_go_live_at"] = self.object.go_live_at
            context["draft_expire_at"] = self.object.expire_at

        # Get active schedule from the scheduled revision's object (if any)
        if self.scheduled_object:
            context["scheduled_go_live_at"] = self.scheduled_object.go_live_at
            context["scheduled_expire_at"] = self.scheduled_object.expire_at

            # Ignore draft schedule if it's the same as the active schedule
            if context["draft_go_live_at"] == context["scheduled_go_live_at"]:
                context["draft_go_live_at"] = None

            if context["draft_expire_at"] == context["scheduled_expire_at"]:
                context["draft_expire_at"] = None

        # The live object can still have its own active expiry date
        # that's separate from the active schedule
        if (
            self.live_object
            and self.live_object.expire_at
            and not self.live_object.expired
        ):
            context["live_expire_at"] = self.live_object.expire_at

            # Ignore the live object's expiry date if the active schedule has
            # an earlier go_live_at, as the active schedule's expiry date will
            # override the live object's expiry date when the draft is published
            if (
                context["scheduled_go_live_at"]
                and context["scheduled_go_live_at"] < context["live_expire_at"]
            ):
                context["live_expire_at"] = None

        # Only show the box for the live object expire_at edge case
        # if it passes the checks above
        context["has_live_publishing_schedule"] = bool(context["live_expire_at"])

        # Only show the main scheduled publishing box if it has at least one of
        # the draft/active schedule dates after passing the checks above
        context["has_draft_publishing_schedule"] = any(
            (
                context["scheduled_go_live_at"],
                context["scheduled_expire_at"],
                context["draft_go_live_at"],
                context["draft_expire_at"],
            )
        )

        return context

    def get_lock_context(self, parent_context):
        self.lock = None
        lock_context = {}
        if self.locking_enabled:
            self.lock = self.object.get_lock()
            if self.lock:
                lock_context = self.lock.get_context_for_user(
                    self.request.user, parent_context
                )
        return {
            "lock": self.lock,
            "user_can_lock": parent_context.get("user_can_lock"),
            "user_can_unlock": parent_context.get("user_can_unlock"),
            "lock_context": lock_context,
        }

    def get_usage_context(self):
        return {
            "usage_count": ReferenceIndex.get_grouped_references_to(
                self.object
            ).count(),
            "usage_url": self.usage_url,
        }

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["locale"] = self.locale
        context["translations"] = self.translations
        if self.translations:
            context["translations_total"] = len(self.translations) + 1
        context["model_name"] = capfirst(self.model._meta.verbose_name)
        context["base_model_name"] = context["model_name"]
        context["history_url"] = self.history_url
        context["status_templates"] = self.get_status_templates(context)
        context["last_updated_info"] = self.last_updated_info
        context.update(self.get_scheduled_publishing_context(parent_context))
        context.update(self.get_lock_context(parent_context))
        if self.object.pk and self.usage_url:
            context.update(self.get_usage_context())
        return context


class PageStatusSidePanel(StatusSidePanel):
    def __init__(self, *args, **kwargs):
        self.parent_page = kwargs.pop("parent_page", None)
        super().__init__(*args, **kwargs)
        if self.object.pk:
            self.usage_url = reverse("wagtailadmin_pages:usage", args=(self.object.pk,))

            permissions = self.object.permissions_for_user(self.request.user)
            if permissions.can_view_revisions():
                self.history_url = reverse(
                    "wagtailadmin_pages:history",
                    args=(self.object.pk,),
                )

    def get_status_templates(self, context):
        templates = super().get_status_templates(context)
        templates.insert(
            -1, "wagtailadmin/shared/side_panels/includes/status/privacy.html"
        )
        return templates

    def get_usage_context(self):
        context = super().get_usage_context()
        context["usage_url_text"] = ngettext(
            "Referenced %(count)s time",
            "Referenced %(count)s times",
            context["usage_count"],
        ) % {"count": context["usage_count"]}
        return context

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        page = self.object

        if self.parent_page:
            context["parent_page"] = self.parent_page

        if page.id:
            context.update(
                {
                    "workflow_history_url": reverse(
                        "wagtailadmin_pages:workflow_history", args=(page.id,)
                    ),
                    "revisions_compare_url_name": "wagtailadmin_pages:revisions_compare",
                    "lock_url": reverse("wagtailadmin_pages:lock", args=(page.id,)),
                    "unlock_url": reverse("wagtailadmin_pages:unlock", args=(page.id,)),
                }
            )

        context.update(
            {
                "model_name": self.model.get_verbose_name(),
                "base_model_name": Page._meta.verbose_name,
                "model_description": self.model.get_page_description(),
                "status_templates": self.get_status_templates(context),
            }
        )

        return context


class CommentsSidePanel(BaseSidePanel):
    class SidePanelToggle(BaseSidePanel.SidePanelToggle):
        aria_label = gettext_lazy("Toggle comments")
        icon_name = "comment"

    name = "comments"
    title = gettext_lazy("Comments")
    template_name = "wagtailadmin/shared/side_panels/comments.html"
    order = 300

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["form"] = parent_context.get("form")
        return context


class ChecksSidePanel(BaseSidePanel):
    class SidePanelToggle(BaseSidePanel.SidePanelToggle):
        aria_label = gettext_lazy("Toggle checks")
        icon_name = "glasses"

    name = "checks"
    title = gettext_lazy("Checks")
    template_name = "wagtailadmin/shared/side_panels/checks.html"
    order = 350

    def get_axe_configuration(self):
        # Retrieve the Axe configuration from the userbar.
        userbar_items = [AccessibilityItem()]
        page = self.object if issubclass(self.model, Page) else None
        apply_userbar_hooks(self.request, userbar_items, page)

        for item in userbar_items:
            if isinstance(item, AccessibilityItem):
                return item.get_axe_configuration(self.request)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["axe_configuration"] = self.get_axe_configuration()
        return context


class PreviewSidePanel(BaseSidePanel):
    class SidePanelToggle(BaseSidePanel.SidePanelToggle):
        aria_label = gettext_lazy("Toggle preview")
        icon_name = "mobile-alt"
        has_counter = False
        keyboard_shortcut = "mod+p"

    name = "preview"
    title = gettext_lazy("Preview")
    template_name = "wagtailadmin/shared/side_panels/preview.html"
    order = 400

    def __init__(self, object, request, *, preview_url):
        super().__init__(object, request)
        self.preview_url = preview_url

    @property
    def auto_update_interval(self):
        if hasattr(settings, "WAGTAIL_AUTO_UPDATE_PREVIEW"):
            warnings.warn(
                "`WAGTAIL_AUTO_UPDATE_PREVIEW` is deprecated. "
                "Set `WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL = 0` to disable "
                "auto-update for previews.",
                RemovedInWagtail70Warning,
            )
            if not settings.WAGTAIL_AUTO_UPDATE_PREVIEW:
                return 0

        return getattr(settings, "WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL", 500)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["preview_url"] = self.preview_url
        context["has_multiple_modes"] = len(self.object.preview_modes) > 1
        context["auto_update_interval"] = self.auto_update_interval
        return context
