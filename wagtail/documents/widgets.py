import json

from django import forms
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import AdminChooser
from wagtail.documents import get_document_model


class AdminDocumentChooser(AdminChooser):
    choose_one_text = _('Choose a document')
    choose_another_text = _('Choose another document')
    link_to_chosen_text = _('Edit this document')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.document_model = get_document_model()

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.document_model, value)
        original_field_html = super().render_html(name, value, attrs)

        return render_to_string("wagtaildocs/widgets/document_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'document': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createDocumentChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtaildocs/js/document-chooser-modal.js'),
            versioned_static('wagtaildocs/js/document-chooser.js'),
        ])
