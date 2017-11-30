from django.utils.functional import cached_property

from wagtail.core.blocks import ChooserBlock
from wagtail.core.utils import resolve_model_string


class SnippetChooserBlock(ChooserBlock):
    def __init__(self, target_model, **kwargs):
        super().__init__(**kwargs)
        self._target_model = target_model

    @cached_property
    def target_model(self):
        return resolve_model_string(self._target_model)

    @cached_property
    def widget(self):
        from wagtail.snippets.widgets import AdminSnippetChooser
        return AdminSnippetChooser(self.target_model)

    class Meta:
        icon = "snippet"
