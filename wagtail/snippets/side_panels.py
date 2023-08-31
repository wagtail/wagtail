from wagtail.admin.ui.side_panels import BaseStatusSidePanel


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
