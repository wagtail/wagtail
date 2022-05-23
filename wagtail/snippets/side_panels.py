from django.forms import Media
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy

from wagtail.admin.ui.components import Component


class BaseSidePanel(Component):
    def get_context_data(self, parent_context):
        # Parent context is a RequestContext, flatten into a plain dictionary
        context = parent_context.flatten()
        context["panel"] = self
        return context


class StatusSidePanel(BaseSidePanel):
    name = "status"
    title = gettext_lazy("Status")
    template_name = "wagtailsnippets/snippets/side_panels/status.html"
    order = 100
    toggle_aria_label = gettext_lazy("Toggle status")
    toggle_icon_name = "info-circle"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        translations = context.get("translations")

        if translations:
            context["translations_total"] = len(translations) + 1

        return context


class SnippetSidePanels:
    def __init__(self):
        self.side_panels = [
            StatusSidePanel(),
        ]

    def __iter__(self):
        return iter(self.side_panels)

    @cached_property
    def media(self):
        media = Media()
        for panel in self.side_panels:
            media += panel.media
        return media
