from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel


class BaseImageChooserPanel(BaseChooserPanel):
    field_template = "wagtailimages/edit_handlers/image_chooser_panel.html"
    object_type_name = "image"
    js_function_name = "createImageChooser"
    edit_link_reverse = "wagtailimages_edit_image"

def ImageChooserPanel(field_name):
    return type('_ImageChooserPanel', (BaseImageChooserPanel,), {
        'field_name': field_name,
    })
