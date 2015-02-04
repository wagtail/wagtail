from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from .widgets import AdminImageChooser


class BaseImageChooserPanel(BaseChooserPanel):
    field_template = "wagtailimages/edit_handlers/image_chooser_panel.html"
    object_type_name = "image"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminImageChooser}


class ImageChooserPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_ImageChooserPanel'), (BaseImageChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
        })
