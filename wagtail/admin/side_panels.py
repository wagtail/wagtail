from django.conf import settings
from django.forms import Media
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy

from wagtail.admin.ui.components import Component
from wagtail.models import UserPagePermissionsProxy


class BaseSidePanel(Component):
    def __init__(self, page, request):
        self.page = page
        self.request = request

    def get_context_data(self, parent_context):
        return {"panel": self, "page": self.page, "request": self.request}


class StatusSidePanel(BaseSidePanel):
    name = "status"
    title = gettext_lazy("Status")
    template_name = "wagtailadmin/pages/side_panels/status.html"
    order = 100
    toggle_aria_label = gettext_lazy("Toggle status")
    toggle_icon_name = "info-circle"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        user_perms = UserPagePermissionsProxy(self.request.user)

        if self.page.id:
            context.update(
                {
                    "lock_url": reverse(
                        "wagtailadmin_pages:lock", args=(self.page.id,)
                    ),
                    "unlock_url": reverse(
                        "wagtailadmin_pages:unlock", args=(self.page.id,)
                    ),
                    "user_can_lock": user_perms.for_page(self.page).can_lock(),
                    "user_can_unlock": user_perms.for_page(self.page).can_unlock(),
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
                    "locale": self.page.locale,
                    "translations": [
                        {
                            "locale": translation.locale,
                            "url": reverse(
                                "wagtailadmin_pages:edit", args=[translation.id]
                            ),
                        }
                        for translation in self.page.get_translations()
                        .only("id", "locale", "depth")
                        .select_related("locale")
                        if user_perms.for_page(translation).can_edit()
                    ],
                }
            )

        return context


class CommentsSidePanel(BaseSidePanel):
    name = "comments"
    title = gettext_lazy("Comments")
    template_name = "wagtailadmin/pages/side_panels/comments.html"
    order = 300
    toggle_aria_label = gettext_lazy("Toggle comments")
    toggle_icon_name = "comment"


class PreviewSidePanel(BaseSidePanel):
    name = "preview"
    title = gettext_lazy("Preview")
    template_name = "wagtailadmin/pages/side_panels/preview.html"
    order = 400
    toggle_aria_label = gettext_lazy("Toggle preview")
    toggle_icon_name = "mobile-alt"


class PageSidePanels:
    def __init__(self, request, page, *, comments_enabled):
        self.request = request
        self.page = page

        self.side_panels = [
            StatusSidePanel(page, self.request),
            # PreviewSidePanel(page),
        ]

        if comments_enabled:
            self.side_panels = self.side_panels + [
                CommentsSidePanel(page, self.request)
            ]

    def __iter__(self):
        return iter(self.side_panels)

    @cached_property
    def media(self):
        media = Media()
        for panel in self.side_panels:
            media += panel.media
        return media
