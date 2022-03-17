from django.utils.functional import cached_property

from wagtail.blocks import ChooserBlock
from wagtail.coreutils import resolve_model_string


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

    def get_form_state(self, value):
        value_data = self.widget.get_value_data(value)
        if value_data is None:
            return None
        else:
            return {
                "id": value_data["id"],
                "edit_link": value_data["edit_url"],
                "string": value_data["string"],
            }

    class Meta:
        icon = "snippet"
