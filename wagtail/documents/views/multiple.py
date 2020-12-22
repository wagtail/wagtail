import os.path

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic import View

from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.search.backends import get_search_backends

from .. import get_document_model
from ..forms import get_document_form, get_document_multi_form
from ..models import UploadedDocument
from ..permissions import permission_policy


permission_checker = PermissionPolicyChecker(permission_policy)


class AddView(View):
    @method_decorator(permission_checker.require('add'))
    @method_decorator(vary_on_headers('X-Requested-With'))
    def dispatch(self, request):
        self.model = get_document_model()
        self.form_class = get_document_form(self.model)
        self.edit_form_class = get_document_multi_form(self.model)

        return super().dispatch(request)

    def post(self, request):
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        form = self.form_class({
            'title': request.FILES['files[]'].name,
            'collection': request.POST.get('collection'),
        }, {
            'file': request.FILES['files[]']
        }, user=request.user)

        if form.is_valid():
            # Save it
            doc = form.save(commit=False)
            doc.uploaded_by_user = request.user
            doc.file_size = doc.file.size

            # Set new document file hash
            doc.file.seek(0)
            doc._set_file_hash(doc.file.read())
            doc.file.seek(0)

            doc.save()

            # Success! Send back an edit form for this document to the user
            return JsonResponse({
                'success': True,
                'doc_id': int(doc.id),
                'form': render_to_string('wagtaildocs/multiple/edit_form.html', {
                    'doc': doc,  # only used for tests
                    'edit_action': reverse('wagtaildocs:edit_multiple', args=(doc.id,)),
                    'delete_action': reverse('wagtaildocs:delete_multiple', args=(doc.id,)),
                    'form': self.edit_form_class(
                        instance=doc, prefix='doc-%d' % doc.id, user=request.user
                    ),
                }, request=request),
            })
        elif 'file' in form.errors:
            # The uploaded file is invalid; reject it now
            return JsonResponse({
                'success': False,
                'error_message': '\n'.join(form.errors['file']),
            })
        else:
            # Some other field of the document form has failed validation, e.g. a required metadata
            # field on a custom document model. Store the document as an UploadedDocument instead
            # and present the edit form so that it will become a proper Document when successfully
            # filled in
            uploaded_doc = UploadedDocument.objects.create(
                file=request.FILES['files[]'], uploaded_by_user=request.user
            )
            doc = self.model(title=request.FILES['files[]'].name, collection_id=request.POST.get('collection'))

            return JsonResponse({
                'success': True,

                'uploaded_document_id': uploaded_doc.id,
                'form': render_to_string('wagtaildocs/multiple/edit_form.html', {
                    'uploaded_document': uploaded_doc,  # only used for tests
                    'edit_action': reverse('wagtaildocs:create_multiple_from_uploaded_document', args=(uploaded_doc.id,)),
                    'delete_action': reverse('wagtaildocs:delete_upload_multiple', args=(uploaded_doc.id,)),
                    'form': self.edit_form_class(
                        instance=doc, prefix='uploaded-document-%d' % uploaded_doc.id, user=request.user
                    ),
                }, request=request),
            })

    def get(self, request):
        # Instantiate a dummy copy of the form that we can retrieve validation messages and media from;
        # actual rendering of forms will happen on AJAX POST rather than here
        form = self.form_class(user=request.user)

        collections = permission_policy.collections_user_has_permission_for(request.user, 'add')
        if len(collections) < 2:
            # no need to show a collections chooser
            collections = None

        return TemplateResponse(request, 'wagtaildocs/multiple/add.html', {
            'help_text': form.fields['file'].help_text,
            'collections': collections,
            'form_media': form.media,
        })


class EditView(View):
    http_method_names = ['post']

    def post(self, request, doc_id, callback=None):
        Document = get_document_model()
        DocumentMultiForm = get_document_multi_form(Document)

        doc = get_object_or_404(Document, id=doc_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not permission_policy.user_has_permission_for_instance(request.user, 'change', doc):
            raise PermissionDenied

        form = DocumentMultiForm(
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

    def post(self, request, doc_id):
        Document = get_document_model()

        doc = get_object_or_404(Document, id=doc_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not permission_policy.user_has_permission_for_instance(request.user, 'delete', doc):
            raise PermissionDenied

        doc.delete()

        return JsonResponse({
            'success': True,
            'doc_id': int(doc_id),
        })


class CreateFromUploadedDocumentView(View):
    http_method_names = ['post']

    def post(self, request, uploaded_document_id):
        Document = get_document_model()
        DocumentMultiForm = get_document_multi_form(Document)

        uploaded_doc = get_object_or_404(UploadedDocument, id=uploaded_document_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if uploaded_doc.uploaded_by_user != request.user:
            raise PermissionDenied

        doc = Document()
        form = DocumentMultiForm(
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
