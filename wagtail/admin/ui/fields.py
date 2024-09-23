from django.core.exceptions import ImproperlyConfigured
from django.db import models

from wagtail.admin.ui.components import Component
from wagtail.utils.registry import ModelFieldRegistry

display_class_registry = ModelFieldRegistry()


def register_display_class(field_class, to=None, display_class=None, exact_class=False):
    """
    Define how model field values should be rendered in the admin.
    The `display_class` should be a subclass of `wagtail.admin.ui.components.Component`
    that takes a single argument in its constructor: the value of the field.

    This is mainly useful for defining how fields are rendered in the inspect view,
    but it can also be used in other places, e.g. listing views.
    """

    if display_class is None:
        raise ImproperlyConfigured(
            "register_display_class must be passed a 'display_class' keyword argument"
        )

    if to and field_class != models.ForeignKey:
        raise ImproperlyConfigured(
            "The 'to' argument on register_display_class is only valid for ForeignKey fields"
        )

    display_class_registry.register(
        field_class, to=to, value=display_class, exact_class=exact_class
    )


class BaseFieldDisplay(Component):
    def __init__(self, value):
        self.value = value

    def get_context_data(self, parent_context):
        return {"value": self.value}
