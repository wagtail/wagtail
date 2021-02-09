import json

from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import AdminChooser
from wagtail.core.telepath import register
from wagtail.core.widget_adapters import WidgetAdapter
from wagtail.documents import get_document_model


class AdminDocumentChooser(AdminChooser):
    choose_one_text = _('Choose a document')
    choose_another_text = _('Choose another document')
    link_to_chosen_text = _('Edit this document')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.document_model = get_document_model()

    def get_value_data(self, value):
        if value is None:
            return None
        elif isinstance(value, self.document_model):
            doc = value
        else:  # assume document ID
            doc = self.document_model.objects.get(pk=value)

        return {
            'id': doc.pk,
            'title': doc.title,
            'edit_url': reverse('wagtaildocs:edit', args=[doc.id]),
        }

    def render_html(self, name, value_data, attrs):
        value_data = value_data or {}
        original_field_html = super().render_html(name, value_data.get('id'), attrs)

        return render_to_string("wagtaildocs/widgets/document_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': bool(value_data),  # only used by chooser.html to identify blank values
            'display_title': value_data.get('title', ''),
            'edit_url': value_data.get('edit_url', ''),
        })

    def render_js_init(self, id_, name, value_data):
        return "createDocumentChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtaildocs/js/document-chooser-modal.js'),
            versioned_static('wagtaildocs/js/document-chooser.js'),
        ])


class DocumentChooserAdapter(WidgetAdapter):
    js_constructor = 'wagtail.documents.widgets.DocumentChooser'

    def js_args(self, widget):
        return [
            widget.render_html('__NAME__', None, attrs={'id': '__ID__'}),
            widget.id_for_label('__ID__'),
        ]

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtaildocs/js/document-chooser-telepath.js'),
        ])


register(DocumentChooserAdapter(), AdminDocumentChooser)
