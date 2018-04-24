from django.utils.html import escape

from wagtail.documents.models import get_document_model


# Front-end conversion

def document_linktype_handler(attrs):
    Document = get_document_model()
    try:
        doc = Document.objects.get(id=attrs['id'])
        return '<a href="%s">' % escape(doc.url)
    except Document.DoesNotExist:
        return "<a>"
