import warnings

import swapper
from django.utils.translation import gettext_lazy as _

from wagtail.admin.views.generic import BaseListingView, PermissionCheckedMixin
from wagtail.admin.views.mixins import SpreadsheetExportMixin
from wagtail.utils.deprecation import removed_in_next_version_warning

Page = swapper.load_model("wagtailcore", "Page")


class ReportView(SpreadsheetExportMixin, PermissionCheckedMixin, BaseListingView):
    template_name = "wagtailadmin/reports/base_report.html"
    results_template_name = "wagtailadmin/reports/base_report_results.html"
    title = ""
    paginate_by = 50

    def get_filtered_queryset(self):
        # Deprecated: kept for backwards compatibility until Wagtail 9.0.
        # The deprecation warning is issued in get(), so it fires exactly
        # once, including for overrides that do not call super().
        return self.get_queryset()

    def decorate_paginated_queryset(self, object_list):
        # A hook point to allow rewriting the object list after pagination has been applied
        return object_list

    def get(self, request, *args, **kwargs):
        if type(self).get_filtered_queryset is not ReportView.get_filtered_queryset:
            # Honour overrides of the deprecated get_filtered_queryset()
            # until Wagtail 9.0, with a deprecation warning issued here so
            # it fires exactly once, including for overrides that do not
            # call super().
            warnings.warn(
                "ReportView.get_filtered_queryset() is deprecated. "
                "Use get_queryset() instead.",
                removed_in_next_version_warning,
                stacklevel=2,
            )
            self.object_list = self.get_filtered_queryset()
        else:
            self.object_list = self.get_queryset()
        context = self.get_context_data()
        # Decorate the queryset *after* Django's BaseListView has returned a paginated/reduced
        # list of objects
        context["object_list"] = self.decorate_paginated_queryset(
            context["object_list"]
        )
        return self.render_to_response(context)

    def render_to_response(self, context, **response_kwargs):
        if self.is_export:
            return self.as_spreadsheet(
                context["object_list"], self.request.GET.get("export")
            )
        return super().render_to_response(context, **response_kwargs)


class PageReportView(ReportView):
    results_template_name = "wagtailadmin/reports/base_page_report_results.html"
    export_headings = {
        "latest_revision_created_at": _("Updated"),
        "status_string": _("Status"),
        "content_type.model_class._meta.verbose_name.title": _("Type"),
    }
    list_export = [
        "title",
        "latest_revision_created_at",
        "status_string",
        "content_type.model_class._meta.verbose_name.title",
    ]
    context_object_name = "pages"
    model = Page
