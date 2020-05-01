from django.utils.functional import cached_property
from django.utils.html import format_html

from wagtail.core.blocks import ChooserBlock


class DocumentChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail.documents import get_document_model
        return get_document_model()

    @cached_property
    def widget(self):
        from wagtail.documents.widgets import AdminDocumentChooser
        return AdminDocumentChooser

    def render_basic(self, value, context=None):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''

    class Meta:
        icon = "doc-empty"
