from django.utils.html import escape

from wagtail.documents.models import get_document_model


# Front-end conversion

class DocumentLinkHandler:
    @staticmethod
    def expand_db_attributes(attrs):
        Document = get_document_model()
        try:
            doc = Document.objects.get(id=attrs['id'])
            return '<a href="%s">' % escape(doc.url)
        except (Document.DoesNotExist, KeyError):
            return "<a>"
