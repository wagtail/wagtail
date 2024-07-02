import datetime
from collections import OrderedDict

from django.contrib.admin.utils import quote
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy
from django_filters import DateFromToRangeFilter

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.views import generic
from wagtail.admin.views.generic.base import BaseListingView
from wagtail.admin.views.mixins import SpreadsheetExportMixin
from wagtail.contrib.forms.utils import get_form_submissions_as_data, get_forms_for_user
from wagtail.models import Page


def get_submissions_list_view(request, *args, **kwargs):
    """Call the form page's list submissions view class"""
    page_id = kwargs.get("page_id")
    form_page = get_object_or_404(Page, id=page_id).specific
    return form_page.serve_submissions_list_view(request, *args, **kwargs)


class ContentTypeColumn(Column):
    edit_url_name = "wagtailadmin_pages:edit"
    cell_template_name = "wagtailforms/content_type_column.html"

    def get_url(self, instance):
        return reverse(self.edit_url_name, args=(quote(instance.pk),))

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["url"] = self.get_url(instance)
        return context


class FormPagesListView(generic.IndexView):
    """Lists the available form pages for the current user"""

    template_name = "wagtailforms/index.html"
    results_template_name = "wagtailforms/index_results.html"
    context_object_name = "form_pages"
    paginate_by = 20
    page_kwarg = "p"
    index_url_name = "wagtailforms:index"
    index_results_url_name = "wagtailforms:index_results"
    page_title = gettext_lazy("Forms")
    header_icon = "form"
    _show_breadcrumbs = True
    columns = [
        TitleColumn(
            "title",
            classname="title",
            label=gettext_lazy("Title"),
            width="50%",
            url_name="wagtailforms:list_submissions",
            sort_key="title",
        ),
        ContentTypeColumn(
            "content_type",
            label=gettext_lazy("Origin"),
            width="50%",
            sort_key="content_type",
        ),
    ]
    model = Page
    is_searchable = False

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items + [
            {"url": "", "label": self.page_title, "sublabel": gettext("Pages")},
        ]

    def get_base_queryset(self):
        """Return the queryset of form pages for this view"""
        return get_forms_for_user(self.request.user).select_related("content_type")


class SubmissionsListFilterSet(WagtailFilterSet):
    date = DateFromToRangeFilter(
        label=gettext_lazy("Submission date"),
        field_name="submit_time",
        widget=DateRangePickerWidget,
    )


class SubmissionsListView(SpreadsheetExportMixin, BaseListingView):
    """Lists submissions for the provided form page"""

    template_name = "wagtailforms/submissions_index.html"
    results_template_name = "wagtailforms/list_submissions.html"
    context_object_name = "submissions"
    form_page = None
    default_ordering = ("-submit_time",)
    ordering_csv = ("submit_time",)  # keep legacy CSV ordering
    orderable_fields = (
        "id",
        "submit_time",
    )  # used to validate ordering in URL
    page_title = gettext_lazy("Form data")
    header_icon = "form"
    paginate_by = 20
    filterset_class = SubmissionsListFilterSet
    forms_index_url_name = "wagtailforms:index"
    index_url_name = "wagtailforms:list_submissions"
    index_results_url_name = "wagtailforms:list_submissions_results"
    _show_breadcrumbs = True
    show_export_buttons = True

    def dispatch(self, request, *args, **kwargs):
        """Check permissions and set the form page"""

        self.form_page = kwargs.get("form_page")

        if not get_forms_for_user(request.user).filter(pk=self.form_page.id).exists():
            raise PermissionDenied

        if self.is_export:
            data_fields = self.form_page.get_data_fields()
            # Set the export fields and the headings for spreadsheet export
            self.list_export = [field for field, label in data_fields]
            self.export_headings = dict(data_fields)

        return super().dispatch(request, *args, **kwargs)

    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs["queryset"] = self.get_base_queryset()
        return kwargs

    def get_base_queryset(self):
        """Return queryset of form submissions"""
        submission_class = self.form_page.get_submission_class()
        queryset = submission_class._default_manager.filter(page=self.form_page)
        return queryset

    def get_validated_ordering(self):
        """Return a dict of field names with ordering labels if ordering is valid"""
        orderable_fields = self.orderable_fields or ()
        ordering = {}
        if self.is_export:
            #  Revert to CSV order_by submit_time ascending for backwards compatibility
            default_ordering = self.ordering_csv or ()
        else:
            default_ordering = self.default_ordering or ()
        if isinstance(default_ordering, str):
            default_ordering = (default_ordering,)
        ordering_strs = self.request.GET.getlist("order_by") or list(default_ordering)
        for order in ordering_strs:
            try:
                _, prefix, field_name = order.rpartition("-")
                if field_name in orderable_fields:
                    ordering[field_name] = (
                        prefix,
                        "descending" if prefix == "-" else "ascending",
                    )
            except (IndexError, ValueError):
                continue  # invalid ordering specified, skip it
        return ordering

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset"""
        ordering = self.get_validated_ordering()
        return [values[0] + name for name, values in ordering.items()]

    def get_filename(self):
        """Returns the base filename for the generated spreadsheet data file"""
        return "{}-export-{}".format(
            self.form_page.slug, datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def render_to_response(self, context, **response_kwargs):
        if self.is_export:
            return self.as_spreadsheet(
                context["submissions"], self.request.GET.get("export")
            )
        return super().render_to_response(context, **response_kwargs)

    def to_row_dict(self, item):
        """Orders the submission dictionary for spreadsheet writing"""
        row_dict = OrderedDict(
            (field, item.get_data().get(field)) for field in self.list_export
        )
        return row_dict

    def get_index_url(self):
        return reverse(self.index_url_name, args=(self.form_page.id,))

    def get_index_results_url(self):
        return reverse(self.index_results_url_name, args=(self.form_page.id,))

    def get_page_subtitle(self):
        return self.form_page.get_admin_display_title()

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items + [
            {
                "url": reverse(self.forms_index_url_name),
                "label": gettext("Forms"),
            },
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            },
        ]

    def get_context_data(self, **kwargs):
        """Return context for view"""
        context = super().get_context_data(**kwargs)
        submissions = context[self.context_object_name]
        data_fields = self.form_page.get_data_fields()
        data_rows = []
        context["submissions"] = submissions
        context["page_title"] = self.page_title
        if not self.is_export:
            (data_headings, data_rows) = get_form_submissions_as_data(
                data_fields=data_fields,
                submissions=submissions,
                orderable_fields=self.orderable_fields,
                ordering_by_field=self.get_validated_ordering(),
            )

            context.update(
                {
                    "app_label": "wagtailforms",
                    "model_name": "formsubmission",
                    "form_page": self.form_page,
                    "data_headings": data_headings,
                    "data_rows": data_rows,
                }
            )
        return context