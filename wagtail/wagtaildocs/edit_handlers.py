from __future__ import absolute_import, unicode_literals

from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.compare import FieldComparison, TextDiff
from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from wagtail.wagtaildocs.models import get_document_model

from .widgets import AdminDocumentChooser


class BaseDocumentChooserPanel(BaseChooserPanel):
    object_type_name = "document"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminDocumentChooser}

    @classmethod
    def get_comparison_class(cls):
        return DocumentFieldComparison


class DocumentChooserPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_DocumentChooserPanel'), (BaseDocumentChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
        })


class DocumentFieldComparison(FieldComparison):
    def htmldiff(self):
        model = get_document_model()
        doc_a = model.objects.filter(id=self.val_a).first()
        doc_b = model.objects.filter(id=self.val_b).first()

        if doc_a != doc_b:
            if doc_a and doc_b:
                # Changed
                return TextDiff([('deletion', doc_a.title), ('addition', doc_b.title)]).to_html()
            elif doc_b:
                # Added
                return TextDiff([('addition', doc_b.title)]).to_html()
            elif doc_a:
                # Removed
                return TextDiff([('deletion', doc_a.title)]).to_html()
        else:
            if doc_a:
                return doc_a.title
            else:
                return _("None")
