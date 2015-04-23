from django.shortcuts import get_object_or_404
from django.conf import settings

from wagtail.utils.sendfile import sendfile

from wagtail.wagtaildocs.models import Document, document_served


def serve(request, document_id, document_filename):
    doc = get_object_or_404(Document, id=document_id)

    # Send document_served signal
    document_served.send(sender=Document, instance=doc, request=request)

    if hasattr(settings, 'SENDFILE_BACKEND'):
        return sendfile(request, doc.file.path, attachment=True, attachment_filename=doc.filename)
    else:
        # Fallback to simple backend if user hasn't specified SENDFILE_BACKEND (will crash by default)
        from sendfile.backends.simple import sendfile as simple_sendfile_backend

        return sendfile(request, doc.file.path, attachment=True, attachment_filename=doc.filename, backend=simple_sendfile_backend)
