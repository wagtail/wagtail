from django.contrib.admin.utils import quote
from django.urls import reverse

from wagtail.admin.ui.side_panels import (
    BasePreviewSidePanel,
    BaseSidePanels,
    BaseStatusSidePanel,
)
from wagtail.models import PreviewableMixin


class SnippetStatusSidePanel(BaseStatusSidePanel):
    def get_status_templates(self, context):
        templates = []

        if self.object.pk:
            templates += [
                "wagtailsnippets/snippets/side_panels/includes/status/workflow.html",
            ]

        if context.get("locale"):
            templates += ["wagtailadmin/shared/side_panels/includes/status/locale.html"]

        return templates

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        inherit = [
            "view",
            "revision_enabled",
            "draftstate_enabled",
            "live_last_updated_info",
            "draft_last_updated_info",
            "locale",
            "translations",
        ]
        context.update({k: parent_context.get(k) for k in inherit})

        translations = context.get("translations")
        if translations:
            context["translations_total"] = len(context["translations"]) + 1

        context["status_templates"] = self.get_status_templates(context)
        return context


class SnippetPreviewSidePanel(BasePreviewSidePanel):
    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        view = parent_context["view"]

        if self.object.pk:
            context["preview_url"] = reverse(
                view.preview_url_name, args=[quote(self.object.pk)]
            )
        else:
            context["preview_url"] = reverse(view.preview_url_name)
        return context


class SnippetSidePanels(BaseSidePanels):
    def __init__(self, request, object, view):
        self.side_panels = []
        if object.pk or view.locale:
            self.side_panels += [
                SnippetStatusSidePanel(object, request),
            ]

        if isinstance(object, PreviewableMixin) and object.is_previewable():
            self.side_panels += [
                SnippetPreviewSidePanel(object, request),
            ]
