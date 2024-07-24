from wagtail.admin.ui.side_panels import StatusSidePanel


class SnippetStatusSidePanel(StatusSidePanel):
    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        inherit = [
            "view",
            "workflow_history_url",
            "revisions_compare_url_name",
            "revision_enabled",
            "draftstate_enabled",
            "lock_url",
            "unlock_url",
            "user_can_lock",
            "user_can_unlock",
        ]
        context.update({k: parent_context.get(k) for k in inherit})

        context["status_templates"] = self.get_status_templates(context)
        return context
