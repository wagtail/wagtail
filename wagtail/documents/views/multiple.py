import os.path

from wagtail.admin.views.generic.multiple_upload import AddView as BaseAddView
from wagtail.admin.views.generic.multiple_upload import (
    CreateFromUploadView as BaseCreateFromUploadView,
)
from wagtail.admin.views.generic.multiple_upload import (
    DeleteUploadView as BaseDeleteUploadView,
)
from wagtail.admin.views.generic.multiple_upload import DeleteView as BaseDeleteView
from wagtail.admin.views.generic.multiple_upload import EditView as BaseEditView

from .. import get_document_model
from ..forms import get_document_form, get_document_multi_form
from ..models import UploadedDocument
from ..permissions import permission_policy


class AddView(BaseAddView):
    permission_policy = permission_policy
    template_name = "wagtaildocs/multiple/add.html"
    upload_model = UploadedDocument

    edit_object_url_name = "wagtaildocs:edit_multiple"
    delete_object_url_name = "wagtaildocs:delete_multiple"
    edit_object_form_prefix = "doc"
    context_object_name = "doc"
    context_object_id_name = "doc_id"

    edit_upload_url_name = "wagtaildocs:create_multiple_from_uploaded_document"
    delete_upload_url_name = "wagtaildocs:delete_upload_multiple"
    edit_upload_form_prefix = "uploaded-document"
    context_upload_name = "uploaded_document"
    context_upload_id_name = "uploaded_document_id"

    def get_model(self):
        return get_document_model()

    def get_upload_form_class(self):
        return get_document_form(self.model)

    def get_edit_form_class(self):
        return get_document_multi_form(self.model)

    def save_object(self, form):
        doc = form.save(commit=False)
        doc.uploaded_by_user = self.request.user
        doc._set_document_file_metadata()
        doc.save()

        return doc

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "max_title_length": self.form.fields["title"].max_length,
            }
        )

        return context


class EditView(BaseEditView):
    permission_policy = permission_policy
    pk_url_kwarg = "doc_id"
    edit_object_form_prefix = "doc"
    context_object_name = "doc"
    context_object_id_name = "doc_id"
    edit_object_url_name = "wagtaildocs:edit_multiple"
    delete_object_url_name = "wagtaildocs:delete_multiple"

    def get_model(self):
        return get_document_model()

    def get_edit_form_class(self):
        return get_document_multi_form(self.model)

    def save_object(self, form):
        form.save()


class DeleteView(BaseDeleteView):
    permission_policy = permission_policy
    pk_url_kwarg = "doc_id"
    context_object_id_name = "doc_id"

    def get_model(self):
        return get_document_model()


class CreateFromUploadedDocumentView(BaseCreateFromUploadView):
    edit_upload_url_name = "wagtaildocs:create_multiple_from_uploaded_document"
    delete_upload_url_name = "wagtaildocs:delete_upload_multiple"
    upload_model = UploadedDocument
    upload_pk_url_kwarg = "uploaded_document_id"
    edit_upload_form_prefix = "uploaded-document"
    context_object_id_name = "doc_id"
    context_upload_name = "uploaded_document"

    def get_model(self):
        return get_document_model()

    def get_edit_form_class(self):
        return get_document_multi_form(self.model)

    def save_object(self, form):
        # assign the file content from uploaded_doc to the image object, to ensure it gets saved to
        # Document's storage

        self.object.file.save(
            os.path.basename(self.upload.file.name), self.upload.file.file, save=False
        )
        self.object.uploaded_by_user = self.request.user

        # form.save() would normally handle writing the image file metadata, but in this case the
        # file handling happens outside the form, so we need to do that manually
        self.object._set_document_file_metadata()
        form.save()


class DeleteUploadView(BaseDeleteUploadView):
    upload_model = UploadedDocument
    upload_pk_url_kwarg = "uploaded_document_id"
