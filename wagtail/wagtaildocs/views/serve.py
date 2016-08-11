from __future__ import absolute_import, unicode_literals

from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import BadHeaderError, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from unidecode import unidecode

from wagtail.utils import sendfile_streaming_backend
from wagtail.utils.sendfile import sendfile
from wagtail.wagtaildocs.models import document_served, get_document_model


def serve(request, document_id, document_filename):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    # Send document_served signal
    document_served.send(sender=Document, instance=doc, request=request)

    try:
        local_path = doc.file.path
    except NotImplementedError:
        local_path = None

    if local_path:

        # Use wagtail.utils.sendfile to serve the file;
        # this provides support for mimetypes, if-modified-since and django-sendfile backends

        if hasattr(settings, 'SENDFILE_BACKEND'):
            return sendfile(request, local_path, attachment=True, attachment_filename=doc.filename)
        else:
            # Fallback to streaming backend if user hasn't specified SENDFILE_BACKEND
            return sendfile(
                request,
                local_path,
                attachment=True,
                attachment_filename=doc.filename,
                backend=sendfile_streaming_backend.sendfile
            )

    else:

        # We are using a storage backend which does not expose filesystem paths
        # (e.g. storages.backends.s3boto.S3BotoStorage).
        # Fall back on pre-sendfile behaviour of reading the file content and serving it
        # as a StreamingHttpResponse

        wrapper = FileWrapper(doc.file)
        response = StreamingHttpResponse(wrapper, content_type='application/octet-stream')

        try:
            response['Content-Disposition'] = 'attachment; filename=%s' % doc.filename
        except BadHeaderError:
            # Unicode filenames can fail on Django <1.8, Python 2 due to
            # https://code.djangoproject.com/ticket/20889 - try with an ASCIIfied version of the name
            response['Content-Disposition'] = 'attachment; filename=%s' % unidecode(doc.filename)

        # FIXME: storage backends are not guaranteed to implement 'size'
        response['Content-Length'] = doc.file.size

        return response
