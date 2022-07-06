from django import forms
from django.utils.functional import cached_property

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooserAdapter
from wagtail.documents.views.chooser import viewset as chooser_viewset
from wagtail.telepath import register

AdminDocumentChooser = chooser_viewset.widget_class


class DocumentChooserAdapter(BaseChooserAdapter):
    js_constructor = "wagtail.documents.widgets.DocumentChooser"

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtaildocs/js/document-chooser-telepath.js"),
            ]
        )


register(DocumentChooserAdapter(), AdminDocumentChooser)
