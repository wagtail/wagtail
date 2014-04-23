from django.shortcuts import get_object_or_404
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse

from wagtail.wagtaildocs.models import Document, doc_serve


def serve(request, document_id, document_filename):
    doc = get_object_or_404(Document, id=document_id)
    wrapper = FileWrapper(doc.file)
    response = HttpResponse(wrapper, content_type='application/octet-stream')

    # TODO: strip out weird characters like semicolons from the filename
    # (there doesn't seem to be an official way of escaping them)
    response['Content-Disposition'] = 'attachment; filename=%s' % doc.filename
    response['Content-Length'] = doc.file.size

    # Send doc_serve signal
    doc_serve.send(sender=doc, request=request)

    return response
