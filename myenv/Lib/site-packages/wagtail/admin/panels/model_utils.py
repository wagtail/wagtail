import functools

from django.forms.models import fields_for_model

from wagtail.admin.forms.models import formfield_for_dbfield

from .field_panel import FieldPanel
from .group import ObjectList


def extract_panel_definitions_from_model_class(model, exclude=None):
    if hasattr(model, "panels"):
        return model.panels

    panels = []

    _exclude = []
    if exclude:
        _exclude.extend(exclude)

    fields = fields_for_model(
        model, exclude=_exclude, formfield_callback=formfield_for_dbfield
    )

    for field_name, field in fields.items():
        try:
            panel_class = field.widget.get_panel()
        except AttributeError:
            panel_class = FieldPanel

        panel = panel_class(field_name)
        panels.append(panel)

    return panels


@functools.lru_cache(maxsize=None)
def get_edit_handler(model):
    """
    Get the panel to use in the Wagtail admin when editing this model.
    """
    if hasattr(model, "edit_handler"):
        # use the edit handler specified on the model class
        panel = model.edit_handler
    else:
        panels = extract_panel_definitions_from_model_class(model)
        panel = ObjectList(panels)

    return panel.bind_to_model(model)
