from django import forms
from django.utils.functional import cached_property

from wagtail.admin.staticfiles import versioned_static
from wagtail.documents.views.chooser import viewset as chooser_viewset
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter

AdminDocumentChooser = chooser_viewset.widget_class


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
