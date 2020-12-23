import os.path

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import View

from wagtail.admin.views.generic.multiple_upload import AddView as BaseAddView
from wagtail.search.backends import get_search_backends

from .. import get_document_model
from ..forms import get_document_form, get_document_multi_form
from ..models import UploadedDocument
from ..permissions import permission_policy


class AddView(BaseAddView):
    permission_policy = permission_policy
    template_name = 'wagtaildocs/multiple/add.html'
    edit_form_template_name = 'wagtaildocs/multiple/edit_form.html'
    upload_model = UploadedDocument

    edit_object_url_name = 'wagtaildocs:edit_multiple'
    delete_object_url_name = 'wagtaildocs:delete_multiple'
    edit_object_form_prefix = 'doc'
    context_object_name = 'doc'
    context_object_id_name = 'doc_id'

    edit_upload_url_name = 'wagtaildocs:create_multiple_from_uploaded_document'
    delete_upload_url_name = 'wagtaildocs:delete_upload_multiple'
    edit_upload_form_prefix = 'uploaded-document'
    context_upload_name = 'uploaded_document'
    context_upload_id_name = 'uploaded_document_id'

    def get_model(self):
        return get_document_model()

    def get_upload_form_class(self):
        return get_document_form(self.model)

    def get_edit_form_class(self):
        return get_document_multi_form(self.model)

    def save_object(self, form):
        doc = form.save(commit=False)
        doc.uploaded_by_user = self.request.user
        doc.file_size = doc.file.size

        # Set new document file hash
        doc.file.seek(0)
        doc._set_file_hash(doc.file.read())
        doc.file.seek(0)

        doc.save()

        return doc


class EditView(View):
    http_method_names = ['post']
    permission_policy = permission_policy

    def get_model(self):
        return get_document_model()

    def get_edit_form_class(self):
        return get_document_multi_form(self.model)

    def post(self, request, doc_id, callback=None):
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        doc = get_object_or_404(self.model, id=doc_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not self.permission_policy.user_has_permission_for_instance(request.user, 'change', doc):
            raise PermissionDenied

        form = self.form_class(
            request.POST, request.FILES, instance=doc, prefix='doc-%d' % doc_id, user=request.user
        )

        if form.is_valid():
            form.save()

            # Reindex the doc to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(doc)

            return JsonResponse({
                'success': True,
                'doc_id': int(doc_id),
            })
        else:
            return JsonResponse({
                'success': False,
                'doc_id': int(doc_id),
                'form': render_to_string('wagtaildocs/multiple/edit_form.html', {
                    'doc': doc,  # only used for tests
                    'edit_action': reverse('wagtaildocs:edit_multiple', args=(doc_id,)),
                    'delete_action': reverse('wagtaildocs:delete_multiple', args=(doc_id,)),
                    'form': form,
                }, request=request),
            })


class DeleteView(View):
    http_method_names = ['post']
    permission_policy = permission_policy

    def get_model(self):
        return get_document_model()

    def post(self, request, doc_id):
        self.model = self.get_model()

        doc = get_object_or_404(self.model, id=doc_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not self.permission_policy.user_has_permission_for_instance(request.user, 'delete', doc):
            raise PermissionDenied

        doc.delete()

        return JsonResponse({
            'success': True,
            'doc_id': int(doc_id),
        })


class CreateFromUploadedDocumentView(View):
    http_method_names = ['post']

    def get_model(self):
        return get_document_model()

    def get_edit_form_class(self):
        return get_document_multi_form(self.model)

    def post(self, request, uploaded_document_id):
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        uploaded_doc = get_object_or_404(UploadedDocument, id=uploaded_document_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if uploaded_doc.uploaded_by_user != request.user:
            raise PermissionDenied

        doc = self.model()
        form = self.form_class(
            request.POST, request.FILES, instance=doc, prefix='uploaded-document-%d' % uploaded_document_id, user=request.user
        )

        if form.is_valid():
            # assign the file content from uploaded_doc to the image object, to ensure it gets saved to
            # Document's storage

            doc.file.save(os.path.basename(uploaded_doc.file.name), uploaded_doc.file.file, save=False)
            doc.uploaded_by_user = request.user
            doc.file_size = doc.file.size
            doc.file.open()
            doc.file.seek(0)
            doc._set_file_hash(doc.file.read())
            doc.file.seek(0)
            form.save()

            uploaded_doc.file.delete()
            uploaded_doc.delete()

            # Reindex the document to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(doc)

            return JsonResponse({
                'success': True,
                'doc_id': doc.id,
            })
        else:
            return JsonResponse({
                'success': False,
                'form': render_to_string('wagtaildocs/multiple/edit_form.html', {
                    'uploaded_document': uploaded_doc,  # only used for tests
                    'edit_action': reverse('wagtaildocs:create_multiple_from_uploaded_document', args=(uploaded_doc.id,)),
                    'delete_action': reverse('wagtaildocs:delete_upload_multiple', args=(uploaded_doc.id,)),
                    'form': form,
                }, request=request),
            })


class DeleteUploadView(View):
    http_method_names = ['post']

    def post(self, request, uploaded_document_id):
        uploaded_doc = get_object_or_404(UploadedDocument, id=uploaded_document_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if uploaded_doc.uploaded_by_user != request.user:
            raise PermissionDenied

        uploaded_doc.file.delete()
        uploaded_doc.delete()

        return JsonResponse({
            'success': True,
        })
