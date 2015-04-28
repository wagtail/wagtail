from django.shortcuts import get_object_or_404
from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse, BadHeaderError

from unidecode import unidecode

from wagtail.wagtaildocs.models import Document, document_served


def serve(request, document_id, document_filename):
    doc = get_object_or_404(Document, id=document_id)
    wrapper = FileWrapper(doc.file)
    response = StreamingHttpResponse(wrapper, content_type='application/octet-stream')

    try:
        response['Content-Disposition'] = 'attachment; filename=%s' % doc.filename
    except BadHeaderError:
        # Unicode filenames can fail on Django <1.8, Python 2 due to
        # https://code.djangoproject.com/ticket/20889 - try with an ASCIIfied version of the name
        response['Content-Disposition'] = 'attachment; filename=%s' % unidecode(doc.filename)

    response['Content-Length'] = doc.file.size

    # Send document_served signal
    document_served.send(sender=doc, request=request)

    return response
