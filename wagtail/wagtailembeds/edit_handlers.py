from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from .widgets import AdminEmbedChooser


class BaseEmbedChooserPanel(BaseChooserPanel):
    object_type_name = "embed"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminEmbedChooser}


class EmbedChooserPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_EmbedChooserPanel'), (BaseEmbedChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
        })
