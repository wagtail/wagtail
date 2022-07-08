from django.conf import settings
from django.forms import Media
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy

from wagtail.admin.ui.components import Component
from wagtail.models import Page, UserPagePermissionsProxy


class BaseSidePanel(Component):
    def __init__(self, object, request):
        self.object = object
        self.request = request
        self.model = type(self.object)

    def get_context_data(self, parent_context):
        context = {"panel": self, "object": self.object, "request": self.request}
        if issubclass(self.model, Page):
            context["page"] = self.object
        return context


class BaseStatusSidePanel(BaseSidePanel):
    name = "status"
    title = gettext_lazy("Status")
    template_name = "wagtailadmin/shared/side_panels/status.html"
    order = 100
    toggle_aria_label = gettext_lazy("Toggle status")
    toggle_icon_name = "info-circle"

    def get_status_templates(self, context):
        templates = []

        if self.object.pk:
            templates += [
                "wagtailadmin/shared/side_panels/includes/status/workflow.html",
            ]

        if context.get("locale"):
            templates += ["wagtailadmin/shared/side_panels/includes/status/locale.html"]

        return templates

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["model_name"] = capfirst(self.model._meta.verbose_name)
        context["status_templates"] = self.get_status_templates(context)
        return context


class PageStatusSidePanel(BaseStatusSidePanel):
    def get_status_templates(self, context):
        templates = super().get_status_templates(context)
        if self.object.pk:
            templates += ["wagtailadmin/shared/side_panels/includes/status/locked.html"]
        templates += ["wagtailadmin/shared/side_panels/includes/status/privacy.html"]
        return templates

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        user_perms = UserPagePermissionsProxy(self.request.user)
        page = self.object

        if page.id:
            context.update(
                {
                    "history_url": reverse(
                        "wagtailadmin_pages:history", args=(page.id,)
                    ),
                    "lock_url": reverse("wagtailadmin_pages:lock", args=(page.id,)),
                    "unlock_url": reverse("wagtailadmin_pages:unlock", args=(page.id,)),
                    "user_can_lock": user_perms.for_page(page).can_lock(),
                    "user_can_unlock": user_perms.for_page(page).can_unlock(),
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
            context.update(
                {
                    "locale": page.locale,
                    "translations": [
                        {
                            "locale": translation.locale,
                            "url": reverse(
                                "wagtailadmin_pages:edit", args=[translation.id]
                            ),
                        }
                        for translation in page.get_translations()
                        .only("id", "locale", "depth")
                        .select_related("locale")
                        if user_perms.for_page(translation).can_edit()
                    ],
                    # The sum of translated pages plus 1 to account for the current page
                    "translations_total": page.get_translations().count() + 1,
                }
            )

        context.update(
            {
                "model_name": self.model.get_verbose_name(),
                "model_description": self.model.get_page_description(),
                "status_templates": self.get_status_templates(context),
            }
        )

        return context


class CommentsSidePanel(BaseSidePanel):
    name = "comments"
    title = gettext_lazy("Comments")
    template_name = "wagtailadmin/shared/side_panels/comments.html"
    order = 300
    toggle_aria_label = gettext_lazy("Toggle comments")
    toggle_icon_name = "comment"


class BasePreviewSidePanel(BaseSidePanel):
    name = "preview"
    title = gettext_lazy("Preview")
    template_name = "wagtailadmin/shared/side_panels/preview.html"
    order = 400
    toggle_aria_label = gettext_lazy("Toggle preview")
    toggle_icon_name = "mobile-alt"

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
    def __init__(self, request, page, *, preview_enabled, comments_enabled):
        super().__init__(request, page)

        self.side_panels = [
            PageStatusSidePanel(page, self.request),
        ]

        if preview_enabled and page.preview_modes:
            self.side_panels += [
                PagePreviewSidePanel(page, self.request),
            ]

        if comments_enabled:
            self.side_panels += [
                CommentsSidePanel(page, self.request),
            ]
