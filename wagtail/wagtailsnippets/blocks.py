from __future__ import absolute_import, unicode_literals

from django.utils.functional import cached_property

from wagtail.wagtailcore.blocks import ChooserBlock
from wagtail.wagtailcore.utils import resolve_model_string


class SnippetChooserBlock(ChooserBlock):
    def __init__(self, target_model, **kwargs):
        super(SnippetChooserBlock, self).__init__(**kwargs)
        self._target_model = target_model

    @cached_property
    def target_model(self):
        return resolve_model_string(self._target_model)

    @cached_property
    def widget(self):
        from wagtail.wagtailsnippets.widgets import AdminSnippetChooser
        return AdminSnippetChooser(self.target_model)

    class Meta:
        icon = "snippet"
