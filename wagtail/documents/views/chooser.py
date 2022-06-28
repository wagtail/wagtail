import json

from django import forms
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, View

from wagtail import hooks
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import Column, DateColumn, Table, TitleColumn
from wagtail.admin.views.generic.chooser import (
    ChooseResultsViewMixin,
    ChosenResponseMixin,
    ChosenViewMixin,
    CreateViewMixin,
    CreationFormMixin,
    ModalPageFurnitureMixin,
)
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.documents.permissions import permission_policy
from wagtail.search import index as search_index


class DocumentChosenResponseMixin(ChosenResponseMixin):
    def get_chosen_response_data(self, document):
        response_data = super().get_chosen_response_data(document)
        response_data.update(
            {
                "url": document.url,
                "filename": document.filename,
            }
        )
        return response_data


class DocumentCreationFormMixin(CreationFormMixin):
    create_action_label = _("Upload")
    create_action_clicked_label = _("Uploading…")
    creation_tab_id = "upload"
    create_url_name = "wagtaildocs:chooser_upload"
    permission_policy = permission_policy

    def get_creation_form_class(self):
        return get_document_form(self.model)

    def get_creation_form_kwargs(self):
        kwargs = super().get_creation_form_kwargs()
        kwargs.update(
            {
                "user": self.request.user,
                "prefix": "document-chooser-upload",
            }
        )
        if self.request.method in ("POST", "PUT"):
            kwargs["instance"] = self.model(uploaded_by_user=self.request.user)

        return kwargs


class DownloadColumn(Column):
    cell_template_name = "wagtaildocs/tables/download_cell.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["download_url"] = instance.url
        return context


class DocumentFilterForm(forms.Form):
    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search")}),
        required=False,
    )

    def __init__(self, *args, collections, **kwargs):
        super().__init__(*args, **kwargs)

        if collections:
            collection_choices = [
                ("", _("All collections"))
            ] + collections.get_indented_choices()
            self.fields["collection_id"] = forms.ChoiceField(
                label=_("Collection"),
                choices=collection_choices,
                required=False,
            )


class BaseDocumentChooseView(ModalPageFurnitureMixin, ContextMixin, View):
    icon = "doc-full-inverse"
    page_title = _("Choose a document")
    results_url_name = "wagtaildocs:chooser_results"
    template_name = "wagtailadmin/generic/chooser/chooser.html"
    results_template_name = "wagtaildocs/chooser/results.html"
    filter_form_class = DocumentFilterForm
    per_page = 10

    def get_object_list(self):
        documents = permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["choose"]
        )
        # allow hooks to modify the queryset
        for hook in hooks.get_hooks("construct_document_chooser_queryset"):
            documents = hook(documents, self.request)

        return documents

    def get_filter_form_class(self):
        return self.filter_form_class

    def get_filter_form(self):
        FilterForm = self.get_filter_form_class()
        return FilterForm(self.request.GET, collections=self.collections)

    def filter_object_list(self, documents, form):
        self.collection_id = form.cleaned_data.get("collection_id")
        if self.collection_id:
            documents = documents.filter(collection=self.collection_id)

        self.search_query = form.cleaned_data.get("q")
        if self.search_query:
            documents = documents.search(self.search_query)
            self.is_searching = True
        else:
            documents = documents.order_by("-created_at")

        return documents

    def get_results_url(self):
        return reverse(self.results_url_name)

    @cached_property
    def collections(self):
        collections = permission_policy.collections_user_has_permission_for(
            self.request.user, "choose"
        )
        if len(collections) < 2:
            return None

        return collections

    @property
    def columns(self):
        columns = [
            TitleColumn(
                "title",
                label=_("Title"),
                url_name="wagtaildocs:document_chosen",
                link_attrs={"data-chooser-modal-choice": True},
            ),
            DownloadColumn("filename", label=_("File")),
            DateColumn("created_at", label=_("Created"), width="16%"),
        ]

        if self.collections:
            columns.insert(2, Column("collection", label=_("Collection")))

        return columns

    def get(self, request):
        self.model = get_document_model()
        self.collection_id = None

        documents = self.get_object_list()
        self.is_searching = False
        self.search_query = None

        self.filter_form = self.get_filter_form()
        if self.filter_form.is_valid():
            documents = self.filter_object_list(documents, self.filter_form)

        paginator = Paginator(documents, per_page=self.per_page)
        self.documents = paginator.get_page(request.GET.get("p"))
        self.table = Table(self.columns, self.documents)

        return self.render_to_response()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "results": self.documents,
                "table": self.table,
                "results_url": self.get_results_url(),
                "is_searching": self.is_searching,
                "search_query": self.search_query,
                "can_create": self.can_create(),
                "collection_id": self.collection_id,
            }
        )

        if context["can_create"]:
            creation_form = self.get_creation_form()
            context.update(self.get_creation_form_context_data(creation_form))

        return context

    def render_to_response(self):
        raise NotImplementedError()


class DocumentChooseViewMixin:
    search_tab_label = _("Search")
    creation_tab_label = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "collections": self.collections,
                "filter_form": self.filter_form,
                "search_tab_label": self.search_tab_label,
                "creation_tab_label": self.creation_tab_label
                or self.create_action_label,
            }
        )
        return context

    def get_response_json_data(self):
        return {
            "step": "choose",
            "tag_autocomplete_url": reverse("wagtailadmin_tag_autocomplete"),
        }

    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            self.template_name,
            None,
            self.get_context_data(),
            json_data=self.get_response_json_data(),
        )


class ChooseView(
    DocumentChooseViewMixin, DocumentCreationFormMixin, BaseDocumentChooseView
):
    pass


class ChooseResultsView(
    ChooseResultsViewMixin, DocumentCreationFormMixin, BaseDocumentChooseView
):
    pass


class DocumentChosenView(ChosenViewMixin, DocumentChosenResponseMixin, View):
    def get(self, request, *args, pk, **kwargs):
        self.model = get_document_model()
        return super().get(request, *args, pk, **kwargs)


class ChooserUploadView(
    CreateViewMixin, DocumentCreationFormMixin, DocumentChosenResponseMixin, View
):
    def dispatch(self, request, *args, **kwargs):
        self.model = get_document_model()
        return super().dispatch(request, *args, **kwargs)

    def save_form(self, form):
        document = form.instance
        document.file_size = document.file.size

        # Set new document file hash
        document.file.seek(0)
        document._set_file_hash(document.file.read())
        document.file.seek(0)

        form.save()

        # Reindex the document to make sure all tags are indexed
        search_index.insert_or_update_object(document)

        return document
