from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminSnippetChooser


class SnippetChooserPanel(BaseChooserPanel):
    object_type_name = 'item'

    def widget_overrides(self):
        return {self.field_name: AdminSnippetChooser(model=self.target_model)}

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
        }))

    def on_model_bound(self):
        super().on_model_bound()
        self.target_model = self.db_field.remote_field.model
