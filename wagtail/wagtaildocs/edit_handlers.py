from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel

from .widgets import AdminDocumentChooser


class DocumentChooserPanel(BaseChooserPanel):
    object_type_name = "document"

    def widget_overrides(self):
        return {self.field_name: AdminDocumentChooser}
