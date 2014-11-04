from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from .widgets import AdminDocumentChooser


class BaseDocumentChooserPanel(BaseChooserPanel):
    field_template = "wagtaildocs/edit_handlers/document_chooser_panel.html"
    object_type_name = "document"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminDocumentChooser}


def DocumentChooserPanel(field_name):
    return type(str('_DocumentChooserPanel'), (BaseDocumentChooserPanel,), {
        'field_name': field_name,
    })
