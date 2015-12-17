from __future__ import unicode_literals

from django.utils.functional import cached_property
from django.utils.html import format_html

from wagtail.wagtailcore.blocks import ChooserBlock


class DocumentChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail.wagtaildocs.models import get_document_model
        return get_document_model()

    @cached_property
    def widget(self):
        from wagtail.wagtaildocs.widgets import AdminDocumentChooser
        return AdminDocumentChooser

    def render_basic(self, value):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''
