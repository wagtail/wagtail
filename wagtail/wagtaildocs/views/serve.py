import mimetypes

from django.shortcuts import get_object_or_404
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse

from wagtail.wagtaildocs.models import Document, document_served


def serve(request, document_id, document_filename):
    doc = get_object_or_404(Document, id=document_id)
    wrapper = FileWrapper(doc.file)
    mimetype = mimetypes.guess_type(doc.filename)[0]
    if mimetype:
        response = HttpResponse(wrapper, content_type=mimetype)
    else:
        response = HttpResponse(wrapper, content_type='application/octet-stream')

    # Make PDFs open in the browser where possible rather than save
    if doc.file_extension == 'pdf':
        response['Content-Disposition'] = 'filename=%s' % doc.filename
    else:
        # TODO: strip out weird characters like semicolons from the filename
        # (there doesn't seem to be an official way of escaping them)
        response['Content-Disposition'] = 'attachment; filename=%s' % doc.filename

    response['Content-Length'] = doc.file.size

    # Send document_served signal
    document_served.send(sender=doc, request=request)

    return response
