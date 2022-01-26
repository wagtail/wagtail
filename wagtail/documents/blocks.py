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
        return AdminDocumentChooser()

    def get_form_state(self, value):
        value_data = self.widget.get_value_data(value)
        if value_data is None:
            return None
        else:
            return {
                'id': value_data['id'],
                'edit_link': value_data['edit_url'],
                'title': value_data['title'],
            }

    def render_basic(self, value, context=None):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''

    class Meta:
        icon = "doc-empty"
