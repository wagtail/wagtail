from __future__ import unicode_literals

from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailadmin.blocks import ChooserBlock

class SnippetChooserBlock(ChooserBlock):
    def __init__(self, target_model, **kwargs):
        super(SnippetChooserBlock, self).__init__(**kwargs)
        self.target_model = target_model

    @cached_property
    def widget(self):
        from wagtail.wagtailsnippets.widgets import AdminSnippetChooser
        content_type = ContentType.objects.get_for_model(self.target_model)
        return AdminSnippetChooser(content_type)
