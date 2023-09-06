from django.contrib.admin.utils import quote
from django.urls import reverse

from wagtail.admin.ui.side_panels import (
    BasePreviewSidePanel,
    BaseStatusSidePanel,
)


class SnippetStatusSidePanel(BaseStatusSidePanel):
    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        inherit = [
            "view",
            "history_url",
            "usage_url",
            "workflow_history_url",
            "revisions_compare_url_name",
            "revision_enabled",
            "draftstate_enabled",
            "live_last_updated_info",
            "locale",
            "translations",
            "lock_url",
            "unlock_url",
            "user_can_lock",
            "user_can_unlock",
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
