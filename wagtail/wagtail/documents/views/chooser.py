from django import forms
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.ui.tables import Column, DateColumn, DownloadColumn
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
from wagtail.admin.widgets import BaseChooser, BaseChooserAdapter
from wagtail.blocks import ChooserBlock
from wagtail.documents import get_document_model, get_document_model_string
from wagtail.documents.permissions import permission_policy


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
        from wagtail.documents.forms import get_document_form

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


class BaseDocumentChooseView(BaseChooseView):
    results_template_name = "wagtaildocs/chooser/results.html"
    per_page = 10
    ordering = "-created_at"
    construct_queryset_hook_name = "construct_document_chooser_queryset"

    def get_object_list(self):
        return self.permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["choose"]
        )

    def get_filter_form(self):
        FilterForm = self.get_filter_form_class()
        return FilterForm(self.request.GET, collections=self.collections)

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
        return super().get(request)


class DocumentChooseViewMixin(ChooseViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collections"] = self.collections
        return context


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


class BaseAdminDocumentChooser(BaseChooser):
    classname = "document-chooser"
    js_constructor = "DocumentChooser"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = get_document_model_string()

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtaildocs/js/document-chooser-modal.js"),
                versioned_static("wagtaildocs/js/document-chooser.js"),
                versioned_static("wagtaildocs/js/document-chooser-telepath.js"),
            ]
        )


class DocumentChooserAdapter(BaseChooserAdapter):
    js_constructor = "wagtail.documents.widgets.DocumentChooser"

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtaildocs/js/document-chooser-modal.js"),
                versioned_static("wagtaildocs/js/document-chooser-telepath.js"),
            ]
        )


class BaseDocumentChooserBlock(ChooserBlock):
    def render_basic(self, value, context=None):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ""


class DocumentChooserViewSet(ChooserViewSet):
    choose_view_class = DocumentChooseView
    choose_results_view_class = DocumentChooseResultsView
    chosen_view_class = DocumentChosenView
    create_view_class = DocumentChooserUploadView
    base_widget_class = BaseAdminDocumentChooser
    widget_telepath_adapter_class = DocumentChooserAdapter
    base_block_class = BaseDocumentChooserBlock
    permission_policy = permission_policy

    icon = "doc-full-inverse"
    choose_one_text = _("Choose a document")
    create_action_label = _("Upload")
    create_action_clicked_label = _("Uploading…")
    choose_another_text = _("Choose another document")
    edit_item_text = _("Edit this document")


viewset = DocumentChooserViewSet(
    "wagtaildocs_chooser",
    model=get_document_model_string(),
    url_prefix="documents/chooser",
)
