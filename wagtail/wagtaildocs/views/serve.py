from django.shortcuts import get_object_or_404

from sendfile import sendfile

from wagtail.wagtaildocs.models import Document, document_served


def serve(request, document_id, document_filename):
    doc = get_object_or_404(Document, id=document_id)

    # Send document_served signal
    document_served.send(sender=Document, instance=doc, request=request)

    return sendfile(request, doc.file.path, attachment=True, attachment_filename=doc.filename)
