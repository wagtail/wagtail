from django.conf import settings
from django.forms import Media
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy, ngettext

from wagtail.admin.ui.components import Component
from wagtail.models import DraftStateMixin, LockableMixin, Page, ReferenceIndex


class BaseSidePanel(Component):
    class SidePanelToggle(Component):
        template_name = "wagtailadmin/shared/side_panel_toggle.html"
        aria_label = ""
        icon_name = ""
        has_counter = True
        counter_classname = ""

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


class BaseStatusSidePanel(BaseSidePanel):
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
        in_explorer=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.show_schedule_publishing_toggle = (
            show_schedule_publishing_toggle and not in_explorer
        )
        self.live_object = live_object
        self.scheduled_object = scheduled_object
        self.in_explorer = in_explorer
        self.locking_enabled = isinstance(self.object, LockableMixin)

    def get_status_templates(self, context):
        templates = ["wagtailadmin/shared/side_panels/includes/status/workflow.html"]

        if context.get("locale"):
            templates.append(
                "wagtailadmin/shared/side_panels/includes/status/locale.html"
            )

        if self.object.pk:
            if self.locking_enabled:
                templates.append(
                    "wagtailadmin/shared/side_panels/includes/status/locked.html"
                )

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
            "usage_count": ReferenceIndex.get_references_to(self.object)
            .group_by_source_object()
            .count(),
            "usage_url": getattr(self.object, "usage_url", None),
        }

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["model_name"] = capfirst(self.model._meta.verbose_name)
        context["base_model_name"] = context["model_name"]
        context["status_templates"] = self.get_status_templates(context)
        context.update(self.get_scheduled_publishing_context(parent_context))
        context.update(self.get_lock_context(parent_context))
        if self.object.pk:
            context.update(self.get_usage_context())
        return context


class PageStatusSidePanel(BaseStatusSidePanel):
    def get_status_templates(self, context):
        templates = super().get_status_templates(context)
        templates.insert(
            -1, "wagtailadmin/shared/side_panels/includes/status/privacy.html"
        )
        return templates

    def get_usage_context(self):
        context = super().get_usage_context()
        context["usage_url"] = reverse(
            "wagtailadmin_pages:usage", args=(self.object.id,)
        )
        context["usage_url_text"] = ngettext(
            "Referenced %(count)s time",
            "Referenced %(count)s times",
            context["usage_count"],
        ) % {"count": context["usage_count"]}
        return context

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        page = self.object

        if page.id:
            context.update(
                {
                    "in_explorer": self.in_explorer,
                    "live_object": self.live_object,
                    "scheduled_object": self.scheduled_object,
                    "history_url": reverse(
                        "wagtailadmin_pages:history", args=(page.id,)
                    ),
                    "workflow_history_url": reverse(
                        "wagtailadmin_pages:workflow_history", args=(page.id,)
                    ),
                    "revisions_compare_url_name": "wagtailadmin_pages:revisions_compare",
                    "lock_url": reverse("wagtailadmin_pages:lock", args=(page.id,)),
                    "unlock_url": reverse("wagtailadmin_pages:unlock", args=(page.id,)),
                    "locale": None,
                    "translations": [],
                }
            )
        else:
            context.update(
                {
                    "locale": None,
                    "translations": [],
                }
            )

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            url_name = "wagtailadmin_pages:edit"
            if self.in_explorer:
                url_name = "wagtailadmin_explore"

            context.update(
                {
                    "locale": page.locale,
                    "translations": [
                        {
                            "locale": translation.locale,
                            "url": reverse(url_name, args=[translation.id]),
                        }
                        for translation in page.get_translations()
                        .only("id", "locale", "depth")
                        .select_related("locale")
                        if translation.permissions_for_user(
                            self.request.user
                        ).can_edit()
                    ],
                    # The sum of translated pages plus 1 to account for the current page
                    "translations_total": page.get_translations().count() + 1,
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


class BasePreviewSidePanel(BaseSidePanel):
    class SidePanelToggle(BaseSidePanel.SidePanelToggle):
        aria_label = gettext_lazy("Toggle preview")
        icon_name = "mobile-alt"
        has_counter = False

    name = "preview"
    title = gettext_lazy("Preview")
    template_name = "wagtailadmin/shared/side_panels/preview.html"
    order = 400

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["has_multiple_modes"] = len(self.object.preview_modes) > 1
        return context


class PagePreviewSidePanel(BasePreviewSidePanel):
    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        if self.object.id:
            context["preview_url"] = reverse(
                "wagtailadmin_pages:preview_on_edit", args=[self.object.id]
            )
        else:
            content_type = parent_context["content_type"]
            parent_page = parent_context["parent_page"]
            context["preview_url"] = reverse(
                "wagtailadmin_pages:preview_on_add",
                args=[content_type.app_label, content_type.model, parent_page.id],
            )
        return context


class BaseSidePanels:
    def __init__(self, request, object):
        self.request = request
        self.object = object

        self.side_panels = [
            BaseStatusSidePanel(object, self.request),
        ]

    def __iter__(self):
        return iter(sorted(self.side_panels, key=lambda p: p.order))

    @cached_property
    def media(self):
        media = Media()
        for panel in self:
            media += panel.media
        return media


class PageSidePanels(BaseSidePanels):
    def __init__(
        self,
        request,
        page,
        *,
        preview_enabled,
        comments_enabled,
        show_schedule_publishing_toggle,
        live_page=None,
        scheduled_page=None,
        in_explorer=False,
    ):
        super().__init__(request, page)

        self.side_panels = [
            PageStatusSidePanel(
                page,
                self.request,
                show_schedule_publishing_toggle=show_schedule_publishing_toggle,
                live_object=live_page,
                scheduled_object=scheduled_page,
                in_explorer=in_explorer,
            ),
        ]

        if preview_enabled and page.is_previewable():
            self.side_panels += [
                PagePreviewSidePanel(page, self.request),
            ]

        if comments_enabled:
            self.side_panels += [
                CommentsSidePanel(page, self.request),
            ]
