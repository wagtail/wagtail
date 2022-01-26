from typing import Any, Mapping

from django.forms import MediaDefiningClass
from django.template import Context
from django.template.loader import get_template


class Component(metaclass=MediaDefiningClass):
    def get_context_data(self, parent_context: Mapping[str, Any]) -> Mapping[str, Any]:
        return {}

    def render_html(self, parent_context: Mapping[str, Any] = None) -> str:
        if parent_context is None:
            parent_context = Context()
        context_data = self.get_context_data(parent_context)
        if context_data is None:
            raise TypeError("Expected a dict from get_context_data, got None")

        template = get_template(self.template_name)
        return template.render(context_data)
