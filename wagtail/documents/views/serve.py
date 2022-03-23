from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_control
from django.views.decorators.http import etag

from wagtail import hooks
from wagtail.documents import get_document_model
from wagtail.documents.models import document_served
from wagtail.forms import PasswordViewRestrictionForm
from wagtail.models import CollectionViewRestriction
from wagtail.utils import sendfile_streaming_backend
from wagtail.utils.sendfile import sendfile


def document_etag(request, document_id, document_filename):
    Document = get_document_model()
    if hasattr(Document, "file_hash"):
        return (
            Document.objects.filter(id=document_id)
            .values_list("file_hash", flat=True)
            .first()
        )


@etag(document_etag)
@cache_control(max_age=3600, public=True)
def serve(request, document_id, document_filename):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    # We want to ensure that the document filename provided in the URL matches the one associated with the considered
    # document_id. If not we can't be sure that the document the user wants to access is the one corresponding to the
    # <document_id, document_filename> pair.
    if doc.filename != document_filename:
        raise Http404("This document does not match the given filename.")

    for fn in hooks.get_hooks("before_serve_document"):
        result = fn(doc, request)
        if isinstance(result, HttpResponse):
            return result

    # Send document_served signal
    document_served.send(sender=Document, instance=doc, request=request)

    try:
        local_path = doc.file.path
    except NotImplementedError:
        local_path = None

    try:
        direct_url = doc.file.url
    except NotImplementedError:
        direct_url = None

    serve_method = getattr(settings, "WAGTAILDOCS_SERVE_METHOD", None)

    # If no serve method has been specified, select an appropriate default for the storage backend:
    # redirect for remote storages (i.e. ones that provide a url but not a local path) and
    # serve_view for all other cases
    if serve_method is None:
        if direct_url and not local_path:
            serve_method = "redirect"
        else:
            serve_method = "serve_view"

    if serve_method in ("redirect", "direct") and direct_url:
        # Serve the file by redirecting to the URL provided by the underlying storage;
        # this saves the cost of delivering the file via Python.
        # For serve_method == 'direct', this view should not normally be reached
        # (the document URL as used in links should point directly to the storage URL instead)
        # but we handle it as a redirect to provide sensible fallback /
        # backwards compatibility behaviour.
        return redirect(direct_url)

    if local_path:

        # Use wagtail.utils.sendfile to serve the file;
        # this provides support for mimetypes, if-modified-since and django-sendfile backends

        sendfile_opts = {
            "attachment": (doc.content_disposition != "inline"),
            "attachment_filename": doc.filename,
            "mimetype": doc.content_type,
        }
        if not hasattr(settings, "SENDFILE_BACKEND"):
            # Fallback to streaming backend if user hasn't specified SENDFILE_BACKEND
            sendfile_opts["backend"] = sendfile_streaming_backend.sendfile

        return sendfile(request, local_path, **sendfile_opts)

    else:

        # We are using a storage backend which does not expose filesystem paths
        # (e.g. storages.backends.s3boto.S3BotoStorage) AND the developer has not allowed
        # redirecting to the file url directly.
        # Fall back on pre-sendfile behaviour of reading the file content and serving it
        # as a StreamingHttpResponse

        wrapper = FileWrapper(doc.file)
        response = StreamingHttpResponse(wrapper, doc.content_type)

        # set filename and filename* to handle non-ascii characters in filename
        # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition
        response["Content-Disposition"] = doc.content_disposition

        # FIXME: storage backends are not guaranteed to implement 'size'
        response["Content-Length"] = doc.file.size

        return response


def authenticate_with_password(request, restriction_id):
    """
    Handle a submission of PasswordViewRestrictionForm to grant view access over a
    subtree that is protected by a PageViewRestriction
    """
    restriction = get_object_or_404(CollectionViewRestriction, id=restriction_id)

    if request.method == "POST":
        form = PasswordViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid():
            return_url = form.cleaned_data["return_url"]

            if not url_has_allowed_host_and_scheme(
                return_url, request.get_host(), request.is_secure()
            ):
                return_url = settings.LOGIN_REDIRECT_URL

            restriction.mark_as_passed(request)
            return redirect(return_url)
    else:
        form = PasswordViewRestrictionForm(instance=restriction)

    action_url = reverse(
        "wagtaildocs_authenticate_with_password", args=[restriction.id]
    )

    password_required_template = getattr(
        settings,
        "DOCUMENT_PASSWORD_REQUIRED_TEMPLATE",
        "wagtaildocs/password_required.html",
    )

    context = {"form": form, "action_url": action_url}
    return TemplateResponse(request, password_required_template, context)
