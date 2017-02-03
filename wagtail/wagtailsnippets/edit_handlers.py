from __future__ import absolute_import, unicode_literals

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel

from .widgets import AdminSnippetChooser


class BaseSnippetChooserPanel(BaseChooserPanel):
    object_type_name = 'item'

    _target_model = None

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminSnippetChooser(model=cls.target_model())}

    @classmethod
    def target_model(cls):
        if cls._target_model is None:
            cls._target_model = cls.model._meta.get_field(cls.field_name).rel.model

        return cls._target_model

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
        }))


class SnippetChooserPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_SnippetChooserPanel'), (BaseSnippetChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
        })
