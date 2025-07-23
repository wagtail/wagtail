import os

from django.contrib.admin.utils import quote
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse as HttpResponse
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.filters import BaseMediaFilterSet
from wagtail.admin.ui.tables import (
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    DownloadColumn,
    Table,
    TitleColumn,
    UsageCountColumn,
)
from wagtail.admin.utils import get_valid_next_url_from_request, set_query_params
from wagtail.admin.views import generic
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.documents.permissions import permission_policy
from wagtail.models import ReferenceIndex

permission_checker = PermissionPolicyChecker(permission_policy)
Document = get_document_model()


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


class DocumentsFilterSet(BaseMediaFilterSet):
    permission_policy = permission_policy

    class Meta:
        model = Document
        fields = []


class IndexView(generic.IndexView):
    permission_policy = permission_policy
    any_permission_required = ["add", "change", "delete"]
    context_object_name = "documents"
    page_title = gettext_lazy("Documents")
    header_icon = "doc-full-inverse"
    page_kwarg = "p"
    paginate_by = 20
    index_url_name = "wagtaildocs:index"
    index_results_url_name = "wagtaildocs:index_results"
    add_url_name = "wagtaildocs:add_multiple"
    edit_url_name = "wagtaildocs:edit"
    template_name = "wagtaildocs/documents/index.html"
    results_template_name = "wagtaildocs/documents/index_results.html"
    default_ordering = "title"
    table_class = DocumentTable
    filterset_class = DocumentsFilterSet
    model = get_document_model()
    add_item_label = gettext_lazy("Add a document")
    show_other_searches = True

    def get_base_queryset(self):
        # Get documents (filtered by user permission)
        documents = self.permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["change", "delete"]
        ).select_related("collection")

        # Annotate with usage count from the ReferenceIndex
        documents = documents.annotate(
            usage_count=ReferenceIndex.usage_count_subquery(self.model)
        )

        return documents

    @cached_property
    def current_collection(self):
        # Upon validation, the cleaned data is a Collection instance
        return self.filters and self.filters.form.cleaned_data.get("collection_id")

    @cached_property
    def columns(self):
        columns = [
            BulkActionsColumn("bulk_actions"),
            TitleColumn(
                "title",
                label=_("Title"),
                sort_key="title",
                get_url=self.get_edit_url,
                get_title_id=lambda doc: f"document_{quote(doc.pk)}_title",
            ),
            DownloadColumn("filename", label=_("File")),
            DateColumn(
                "created_at",
                label=_("Created"),
                sort_key="created_at",
            ),
            UsageCountColumn(
                "usage_count",
                label=_("Usage"),
                width="16%",
                sort_key="usage_count",
            ),
        ]
        if self.filters and "collection_id" in self.filters.filters:
            columns.insert(
                3,
                Column("collection", label=_("Collection"), accessor="collection.name"),
            )
        return columns

    @cached_property
    def collections(self):
        collections = permission_policy.collections_user_has_any_permission_for(
            self.request.user, ["add", "change"]
        )
        if len(collections) < 2:
            collections = None
        return collections

    def get_next_url(self):
        next_url = self.index_url
        request_query_string = self.request.META.get("QUERY_STRING")
        if request_query_string:
            next_url += "?" + request_query_string
        return next_url

    def get_add_url(self):
        # Pass the collection filter to prefill the add form's collection field
        return set_query_params(
            super().get_add_url(),
            {"collection_id": self.current_collection and self.current_collection.pk},
        )

    def get_edit_url(self, instance):
        return set_query_params(
            super().get_edit_url(instance),
            {"next": self.get_next_url()},
        )

    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs["is_searching"] = self.is_searching
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_collection"] = self.current_collection
        return context


class CreateView(generic.CreateView):
    permission_policy = permission_policy
    index_url_name = "wagtaildocs:index"
    add_url_name = "wagtaildocs:add"
    edit_url_name = "wagtaildocs:edit"
    error_message = gettext_lazy("The document could not be created due to errors.")
    template_name = "wagtaildocs/documents/add.html"
    header_icon = "doc-full-inverse"

    @cached_property
    def model(self):
        # Use a property instead of setting this as a class attribute so it is
        # accessed at request-time, thus can be tested with override_settings
        return get_document_model()

    def get_form_class(self):
        return get_document_form(self.model)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial_form_instance(self):
        return self.model(uploaded_by_user=self.request.user)

    def get_success_message(self, instance):
        return _("Document '%(document_title)s' added.") % {
            "document_title": instance.title
        }


class EditView(generic.EditView):
    permission_policy = permission_policy
    pk_url_kwarg = "document_id"
    error_message = gettext_lazy("The document could not be saved due to errors.")
    template_name = "wagtaildocs/documents/edit.html"
    index_url_name = "wagtaildocs:index"
    edit_url_name = "wagtaildocs:edit"
    delete_url_name = "wagtaildocs:delete"
    header_icon = "doc-full-inverse"
    context_object_name = "document"

    @cached_property
    def model(self):
        return get_document_model()

    def get_form_class(self):
        return get_document_form(self.model)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.permission_policy.user_has_permission_for_instance(
            self.request.user, self.permission_required, obj
        ):
            raise PermissionDenied
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_message(self):
        return _("Document '%(document_title)s' updated") % {
            "document_title": self.object.title
        }

    @cached_property
    def next_url(self):
        return get_valid_next_url_from_request(self.request)

    def get_success_url(self):
        return self.next_url or super().get_success_url()

    def get_delete_url(self):
        delete_url = super().get_delete_url()
        if self.next_url:
            delete_url += "?" + urlencode({"next": self.next_url})
        return delete_url

    def render_to_response(self, context, **response_kwargs):
        if self.object.is_stored_locally():
            # Give error if document file doesn't exist
            if not os.path.isfile(self.object.file.path):
                messages.error(
                    self.request,
                    _(
                        "The file could not be found. Please change the source or delete the document"
                    ),
                    buttons=[messages.button(self.get_delete_url(), _("Delete"))],
                )

        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage_count_val"] = self.object.get_usage().count()
        context["filesize"] = self.object.get_file_size()
        context["next"] = self.next_url
        return context


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
    index_url_name = "wagtaildocs:index"
    edit_url_name = "wagtaildocs:edit"

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, permission, self.object
        )

    def get_page_subtitle(self):
        return self.object.title
