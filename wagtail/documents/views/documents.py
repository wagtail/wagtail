import os

from django.contrib.admin.utils import quote
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.ui.tables import (
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    DownloadColumn,
    Table,
    TitleColumn,
)
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.views import generic
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.documents.permissions import permission_policy
from wagtail.models import Collection
from wagtail.search.backends import get_search_backend

permission_checker = PermissionPolicyChecker(permission_policy)


class BulkActionsColumn(BulkActionsCheckboxColumn):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, obj_type="document", **kwargs)

    def get_header_context_data(self, parent_context):
        context = super().get_header_context_data(parent_context)
        parent = parent_context.get("current_collection")
        if parent:
            context["parent"] = parent.id
        return context


class DocumentTable(Table):
    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["current_collection"] = parent_context.get("current_collection")
        return context


class BaseListingView(generic.PermissionCheckedMixin, generic.BaseListingView):
    permission_policy = permission_policy
    any_permission_required = ["add", "change", "delete"]
    context_object_name = "documents"
    page_kwarg = "p"
    paginate_by = 20
    index_url_name = "wagtaildocs:index"
    default_ordering = "title"
    table_class = DocumentTable

    def get_queryset(self):
        # Get documents (filtered by user permission)
        documents = self.permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["change", "delete"]
        )
        self.ordering = self.get_ordering()
        documents = documents.order_by(self.ordering)

        # Filter by collection
        self.current_collection = None
        collection_id = self.request.GET.get("collection_id")
        if collection_id:
            try:
                self.current_collection = Collection.objects.get(id=collection_id)
                documents = documents.filter(collection=self.current_collection)
            except (ValueError, Collection.DoesNotExist):
                pass

        # Search
        self.query_string = None
        if "q" in self.request.GET:
            self.form = SearchForm(self.request.GET, placeholder=_("Search documents"))
            if self.form.is_valid():
                self.query_string = self.form.cleaned_data["q"]
                if self.query_string:
                    search_backend = get_search_backend()
                    documents = search_backend.autocomplete(
                        self.query_string, documents
                    )
        else:
            self.form = SearchForm(placeholder=_("Search documents"))

        return documents

    @cached_property
    def columns(self):
        return [
            BulkActionsColumn("bulk_actions"),
            TitleColumn(
                "title",
                label=_("Title"),
                sort_key="title",
                get_url=self.get_edit_url,
                get_title_id=lambda doc: f"document_{quote(doc.pk)}_title",
            ),
            DownloadColumn("filename", label=_("File")),
            Column("collection", label=_("Collection"), accessor="collection.name"),
            DateColumn("created_at", label=_("Created"), sort_key="created_at"),
        ]

    def get_edit_url(self, instance):
        edit_url = reverse("wagtaildocs:edit", args=(quote(instance.pk),))
        next_url = reverse(self.index_url_name)
        request_query_string = self.request.META.get("QUERY_STRING")
        if request_query_string:
            next_url += "?" + request_query_string

        return f"{edit_url}?{urlencode({'next': next_url})}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "query_string": self.query_string,
                "is_searching": bool(self.query_string),
            }
        )
        return context


class IndexView(BaseListingView):
    template_name = "wagtaildocs/documents/index.html"

    @cached_property
    def columns(self):
        columns = super().columns
        if not self.collections:
            columns.pop(3)
        return columns

    @cached_property
    def collections(self):
        collections = permission_policy.collections_user_has_any_permission_for(
            self.request.user, ["add", "change"]
        )
        if len(collections) < 2:
            collections = None
        return collections

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        Document = get_document_model()

        context.update(
            {
                "search_form": self.form,
                "popular_tags": popular_tags_for_model(get_document_model()),
                "user_can_add": permission_policy.user_has_permission(
                    self.request.user, "add"
                ),
                "collections": self.collections,
                "current_collection": self.current_collection,
                "app_label": Document._meta.app_label,
                "model_name": Document._meta.model_name,
            }
        )
        return context


class ListingResultsView(BaseListingView):
    template_name = "wagtaildocs/documents/results.html"


@permission_checker.require("add")
def add(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.method == "POST":
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(
            request.POST, request.FILES, instance=doc, user=request.user
        )
        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("Document '%(document_title)s' added.")
                % {"document_title": doc.title},
                buttons=[
                    messages.button(
                        reverse("wagtaildocs:edit", args=(doc.id,)), _("Edit")
                    )
                ],
            )
            return redirect("wagtaildocs:index")
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(user=request.user)

    return TemplateResponse(
        request,
        "wagtaildocs/documents/add.html",
        {
            "form": form,
        },
    )


@permission_checker.require("change")
def edit(request, document_id):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    doc = get_object_or_404(Document, id=document_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, "change", doc
    ):
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == "POST":
        form = DocumentForm(
            request.POST, request.FILES, instance=doc, user=request.user
        )
        if form.is_valid():
            doc = form.save()

            edit_url = reverse("wagtaildocs:edit", args=(doc.id,))
            redirect_url = "wagtaildocs:index"
            if next_url:
                edit_url = f"{edit_url}?{urlencode({'next': next_url})}"
                redirect_url = next_url

            messages.success(
                request,
                _("Document '%(document_title)s' updated")
                % {"document_title": doc.title},
                buttons=[messages.button(edit_url, _("Edit"))],
            )
            return redirect(redirect_url)
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(instance=doc, user=request.user)

    try:
        local_path = doc.file.path
    except NotImplementedError:
        # Document is hosted externally (eg, S3)
        local_path = None

    if local_path:
        # Give error if document file doesn't exist
        if not os.path.isfile(local_path):
            messages.error(
                request,
                _(
                    "The file could not be found. Please change the source or delete the document"
                ),
                buttons=[
                    messages.button(
                        reverse("wagtaildocs:delete", args=(doc.id,)), _("Delete")
                    )
                ],
            )

    return TemplateResponse(
        request,
        "wagtaildocs/documents/edit.html",
        {
            "document": doc,
            "filesize": doc.get_file_size(),
            "form": form,
            "user_can_delete": permission_policy.user_has_permission_for_instance(
                request.user, "delete", doc
            ),
            "next": next_url,
        },
    )


class DeleteView(generic.DeleteView):
    model = get_document_model()
    pk_url_kwarg = "document_id"
    permission_policy = permission_policy
    permission_required = "delete"
    header_icon = "doc-full-inverse"
    usage_url_name = "wagtaildocs:document_usage"
    delete_url_name = "wagtaildocs:delete"
    index_url_name = "wagtaildocs:index"
    page_title = gettext_lazy("Delete document")

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, permission, self.object
        )

    @property
    def confirmation_message(self):
        # This message will only appear in the singular, but we specify a plural
        # so it can share the translation string with confirm_bulk_delete.html
        return ngettext(
            "Are you sure you want to delete this document?",
            "Are you sure you want to delete these documents?",
            1,
        )

    def get_success_message(self):
        return _("Document '%(document_title)s' deleted.") % {
            "document_title": self.object.title
        }


class UsageView(generic.UsageView):
    model = get_document_model()
    pk_url_kwarg = "document_id"
    permission_policy = permission_policy
    permission_required = "change"
    header_icon = "doc-full-inverse"

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, permission, self.object
        )

    def get_page_subtitle(self):
        return self.object.title
