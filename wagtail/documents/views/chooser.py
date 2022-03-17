from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import View

from wagtail import hooks
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import Column, DateColumn, Table, TitleColumn
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.documents.permissions import permission_policy
from wagtail.search import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)


def get_document_chosen_response(request, document):
    """
    helper function: given a document, return the modal workflow response that returns that
    document back to the calling page
    """
    return render_modal_workflow(
        request,
        None,
        None,
        None,
        json_data={
            "step": "document_chosen",
            "result": {
                "id": document.id,
                "title": document.title,
                "url": document.url,
                "filename": document.filename,
                "edit_link": reverse("wagtaildocs:edit", args=(document.id,)),
            },
        },
    )


class DownloadColumn(Column):
    cell_template_name = "wagtaildocs/tables/download_cell.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["download_url"] = instance.url
        return context


class BaseChooseView(View):
    def get(self, request):
        Document = get_document_model()

        if permission_policy.user_has_permission(request.user, "add"):
            DocumentForm = get_document_form(Document)
            self.uploadform = DocumentForm(
                user=request.user, prefix="document-chooser-upload"
            )
        else:
            self.uploadform = None

        documents = permission_policy.instances_user_has_any_permission_for(
            request.user, ["choose"]
        )

        # allow hooks to modify the queryset
        for hook in hooks.get_hooks("construct_document_chooser_queryset"):
            documents = hook(documents, request)

        self.q = None
        self.is_searching = False

        self.collection_id = request.GET.get("collection_id")
        if self.collection_id:
            documents = documents.filter(collection=self.collection_id)
        self.documents_exist = documents.exists()

        if "q" in request.GET:
            self.searchform = SearchForm(request.GET)
            if self.searchform.is_valid():
                self.q = self.searchform.cleaned_data["q"]

                documents = documents.search(self.q)
                self.is_searching = True
        else:
            self.searchform = SearchForm()

        if not self.is_searching:
            documents = documents.order_by("-created_at")

        paginator = Paginator(documents, per_page=10)
        self.documents = paginator.get_page(request.GET.get("p"))

        self.collections = permission_policy.collections_user_has_permission_for(
            request.user, "choose"
        )
        if len(self.collections) < 2:
            self.collections = None

        columns = [
            TitleColumn(
                "title",
                label=_("Title"),
                url_name="wagtaildocs:document_chosen",
                link_classname="document-choice",
            ),
            DownloadColumn("filename", label=_("File")),
            DateColumn("created_at", label=_("Created"), width="16%"),
        ]

        if self.collections:
            columns.insert(2, Column("collection", label=_("Collection")))

        self.table = Table(columns, self.documents)

        return self.render_to_response()

    def get_context_data(self):
        return {
            "documents": self.documents,
            "documents_exist": self.documents_exist,
            "table": self.table,
            "uploadform": self.uploadform,
            "query_string": self.q,
            "searchform": self.searchform,
            "collections": self.collections,
            "is_searching": self.is_searching,
            "collection_id": self.collection_id,
        }

    def render_to_response(self):
        raise NotImplementedError()


class ChooseView(BaseChooseView):
    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            "wagtaildocs/chooser/chooser.html",
            None,
            self.get_context_data(),
            json_data={
                "step": "chooser",
                "error_label": _("Server Error"),
                "error_message": _(
                    "Report this error to your website administrator with the following information:"
                ),
                "tag_autocomplete_url": reverse("wagtailadmin_tag_autocomplete"),
            },
        )


class ChooseResultsView(BaseChooseView):
    def render_to_response(self):
        return TemplateResponse(
            self.request, "wagtaildocs/chooser/results.html", self.get_context_data()
        )


def document_chosen(request, document_id):
    document = get_object_or_404(get_document_model(), id=document_id)
    return get_document_chosen_response(request, document)


@permission_checker.require("add")
def chooser_upload(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.method == "POST":
        document = Document(uploaded_by_user=request.user)
        form = DocumentForm(
            request.POST,
            request.FILES,
            instance=document,
            user=request.user,
            prefix="document-chooser-upload",
        )

        if form.is_valid():
            document.file_size = document.file.size

            # Set new document file hash
            document.file.seek(0)
            document._set_file_hash(document.file.read())
            document.file.seek(0)

            form.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(document)
            return get_document_chosen_response(request, document)
    else:
        form = DocumentForm(user=request.user, prefix="document-chooser-upload")

    return render_modal_workflow(
        request,
        None,
        None,
        None,
        json_data={
            "step": "reshow_upload_form",
            "htmlFragment": render_to_string(
                "wagtaildocs/chooser/upload_form.html", {"form": form}, request
            ),
        },
    )
