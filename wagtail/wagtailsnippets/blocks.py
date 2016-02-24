from __future__ import unicode_literals

from django.utils.functional import cached_property

from wagtail.wagtailcore.blocks import ChooserBlock


class SnippetChooserBlock(ChooserBlock):
    def __init__(self, target_model, **kwargs):
        super(SnippetChooserBlock, self).__init__(**kwargs)
        self.target_model = target_model

    @cached_property
    def widget(self):
        from wagtail.wagtailsnippets.widgets import AdminSnippetChooser
        return AdminSnippetChooser(self.target_model)
