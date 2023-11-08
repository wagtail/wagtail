from typing import Any, MutableMapping

from django.forms import Media, MediaDefiningClass
from django.template import Context
from django.template.loader import get_template


class Component(metaclass=MediaDefiningClass):
    def get_context_data(
        self, parent_context: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        return {}

    def render_html(self, parent_context: MutableMapping[str, Any] = None) -> str:
        if parent_context is None:
            parent_context = Context()
        context_data = self.get_context_data(parent_context)
        if context_data is None:
            raise TypeError("Expected a dict from get_context_data, got None")

        template = get_template(self.template_name)
        return template.render(context_data)


class MediaContainer(list):
    """
    A list that provides a ``media`` property that combines the media definitions
    of its members.
    """

    @property
    def media(self):
        media = Media()
        for item in self:
            media += item.media
        return media
