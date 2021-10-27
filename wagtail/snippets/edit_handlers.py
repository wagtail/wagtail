from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminSnippetChooser


class SnippetChooserPanel(BaseChooserPanel):
    def widget_overrides(self):
        return {self.field_name: AdminSnippetChooser(model=self.target_model)}

    def on_model_bound(self):
        super().on_model_bound()
        self.target_model = self.db_field.remote_field.model
