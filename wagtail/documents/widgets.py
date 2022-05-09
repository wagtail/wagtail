import json

from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser
from wagtail.documents import get_document_model
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter


class AdminDocumentChooser(BaseChooser):
    choose_one_text = _("Choose a document")
    choose_another_text = _("Choose another document")
    link_to_chosen_text = _("Edit this document")
    chooser_modal_url_name = "wagtaildocs:chooser"
    icon = "doc-full-inverse"
    classname = "document-chooser"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = get_document_model()

    def render_js_init(self, id_, name, value_data):
        return "createDocumentChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtaildocs/js/document-chooser-modal.js"),
                versioned_static("wagtaildocs/js/document-chooser.js"),
            ]
        )


class DocumentChooserAdapter(WidgetAdapter):
    js_constructor = "wagtail.documents.widgets.DocumentChooser"

    def js_args(self, widget):
        return [
            widget.render_html("__NAME__", None, attrs={"id": "__ID__"}),
            widget.id_for_label("__ID__"),
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtaildocs/js/document-chooser-telepath.js"),
            ]
        )


register(DocumentChooserAdapter(), AdminDocumentChooser)
