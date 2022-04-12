from django.forms import Media
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy

from wagtail.admin.ui.components import Component


class BaseSidePanel(Component):
    def __init__(self, page):
        self.page = page

    def get_context_data(self, parent_context):
        return {"panel": self, "page": self.page}


class StatusSidePanel(BaseSidePanel):
    name = "status"
    title = gettext_lazy("Status")
    template_name = "wagtailadmin/pages/side_panels/status.html"
    order = 100
    toggle_aria_label = gettext_lazy("Toggle status")
    toggle_icon_name = "info-circle"


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
    def __init__(self, request, page):
        self.request = request
        self.page = page

        if page:
            # Editing
            self.side_panels = [
                StatusSidePanel(page),
                CommentsSidePanel(page),
                # PreviewSidePanel(page),
            ]
        else:
            # Creating
            self.side_panels = [
                StatusSidePanel(page),
                CommentsSidePanel(page),
            ]

    def __iter__(self):
        return iter(self.side_panels)

    @cached_property
    def media(self):
        media = Media()
        for panel in self.side_panels:
            media += panel.media
        return media
