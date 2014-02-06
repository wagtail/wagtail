from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel


class BaseDocumentChooserPanel(BaseChooserPanel):
    field_template = "wagtaildocs/edit_handlers/document_chooser_panel.html"
    object_type_name = "document"
    js_function_name = "createDocumentChooser"


def DocumentChooserPanel(field_name):
    return type('_DocumentChooserPanel', (BaseDocumentChooserPanel,), {
        'field_name': field_name,
    })
