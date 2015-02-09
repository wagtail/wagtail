from __future__ import absolute_import, unicode_literals

import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser
from wagtail.wagtaildocs.models import Document


class AdminDocumentChooser(AdminChooser):
    choose_one_text = _('Choose a document')
    choose_another_text = _('Choose another document')

    def render_html(self, name, value, attrs):
        original_field_html = super(AdminDocumentChooser, self).render_html(name, value, attrs)

        instance = self.get_instance(Document, value)

        return render_to_string("wagtaildocs/widgets/document_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'document': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createDocumentChooser({0});".format(json.dumps(id_))
