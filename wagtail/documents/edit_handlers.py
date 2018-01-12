from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminDocumentChooser


class DocumentChooserPanel(BaseChooserPanel):
    object_type_name = "document"

    def widget_overrides(self):
        return {self.field_name: AdminDocumentChooser}
