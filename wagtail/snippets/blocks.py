from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property

from wagtail.blocks import ChooserBlock
from wagtail.coreutils import resolve_model_string


class SnippetChooserBlock(ChooserBlock):
    # Blocks are instantiated before models are loaded, so we can't set
    # self.meta.icon in __init__. We need to override the default value
    # some time after the model is loaded, so we mark it as a mutable
    # attribute and set it using set_meta_options.
    MUTABLE_META_ATTRIBUTES = ["icon"]

    def __init__(self, target_model, **kwargs):
        super().__init__(**kwargs)
        self._target_model = target_model

    @cached_property
    def target_model(self):
        return resolve_model_string(self._target_model)

    @cached_property
    def widget(self):
        from wagtail.snippets.widgets import AdminSnippetChooser

        try:
            icon = self.target_model.snippet_viewset.icon
        except AttributeError as e:
            raise ImproperlyConfigured(
                f"Cannot use SnippetChooserBlock with non-snippet model {self.target_model}"
            ) from e

        # Override the default icon with the icon for the target model
        self.set_meta_options({"icon": icon})
        return AdminSnippetChooser(self.target_model, icon=self.meta.icon)

    class Meta:
        icon = "snippet"
