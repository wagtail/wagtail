import json

from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
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
        document, value = self.get_instance_and_id(self.document_model, value)
        original_field_html = super().render_html(name, value, attrs)

        # # Must import here because doing so at the top of the file is too early in the bootstrap.
        # from wagtail.documents.permissions import permission_policy
        # if not permission_policy.user_has_permission_for_instance(user, 'change', instance):
        #     self.show_edit_link = False

        return render_to_string("wagtaildocs/widgets/document_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'display_title': document.title if document else '',
            'edit_url': reverse('wagtaildocs:edit', args=[document.id]) if document else '',
        })

    def render_js_init(self, id_, name, value):
        return "createDocumentChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtaildocs/js/document-chooser-modal.js'),
            versioned_static('wagtaildocs/js/document-chooser.js'),
        ])
