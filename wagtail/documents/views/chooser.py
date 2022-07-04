import json

from django import forms
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from wagtail import hooks
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.views.generic.chooser import (
    BaseChooseView,
    ChooseResultsViewMixin,
    ChooseViewMixin,
    ChosenResponseMixin,
    ChosenViewMixin,
    CreateViewMixin,
    CreationFormMixin,
)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.widgets import BaseChooser
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
    creation_tab_id = "upload"

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


class BaseDocumentChooseView(BaseChooseView):
    results_template_name = "wagtaildocs/chooser/results.html"
    filter_form_class = DocumentFilterForm
    per_page = 10

    def get_object_list(self):
        documents = self.permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["choose"]
        )
        # allow hooks to modify the queryset
        for hook in hooks.get_hooks("construct_document_chooser_queryset"):
            documents = hook(documents, self.request)

        return documents

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

    @cached_property
    def collections(self):
        collections = self.permission_policy.collections_user_has_permission_for(
            self.request.user, "choose"
        )
        if len(collections) < 2:
            return None

        return collections

    @property
    def columns(self):
        columns = super().columns + [
            DownloadColumn("filename", label=_("File")),
            DateColumn("created_at", label=_("Created"), width="16%"),
        ]

        if self.collections:
            columns.insert(2, Column("collection", label=_("Collection")))

        return columns

    def get(self, request):
        self.model = get_document_model()
        self.collection_id = None

        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collection_id"] = self.collection_id
        return context


class DocumentChooseViewMixin(ChooseViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collections"] = self.collections
        return context

    def get_response_json_data(self):
        json_data = super().get_response_json_data()
        json_data["tag_autocomplete_url"] = reverse("wagtailadmin_tag_autocomplete")
        return json_data


class DocumentChooseView(
    DocumentChooseViewMixin, DocumentCreationFormMixin, BaseDocumentChooseView
):
    pass


class DocumentChooseResultsView(
    ChooseResultsViewMixin, DocumentCreationFormMixin, BaseDocumentChooseView
):
    pass


class DocumentChosenView(ChosenViewMixin, DocumentChosenResponseMixin, View):
    def get(self, request, *args, pk, **kwargs):
        self.model = get_document_model()
        return super().get(request, *args, pk, **kwargs)


class DocumentChooserUploadView(
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


class BaseAdminDocumentChooser(BaseChooser):
    classname = "document-chooser"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = get_document_model()

    def render_js_init(self, id_, name, value_data):
        return "createDocumentChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtaildocs/js/document-chooser-modal.js"),
                versioned_static("wagtaildocs/js/document-chooser.js"),
            ]
        )


class DocumentChooserViewSet(ChooserViewSet):
    choose_view_class = DocumentChooseView
    choose_results_view_class = DocumentChooseResultsView
    chosen_view_class = DocumentChosenView
    create_view_class = DocumentChooserUploadView
    base_widget_class = BaseAdminDocumentChooser
    permission_policy = permission_policy

    icon = "doc-full-inverse"
    choose_one_text = _("Choose a document")
    create_action_label = _("Upload")
    create_action_clicked_label = _("Uploading…")
    choose_another_text = _("Choose another document")
    edit_item_text = _("Edit this document")


viewset = DocumentChooserViewSet(
    "wagtaildocs_chooser",
    model=get_document_model(),
    url_prefix="documents/chooser",
)
