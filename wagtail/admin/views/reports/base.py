from warnings import warn

from django.utils.translation import gettext_lazy as _

from wagtail.admin.views.generic import BaseListingView, PermissionCheckedMixin
from wagtail.admin.views.mixins import SpreadsheetExportMixin
from wagtail.permissions import page_permission_policy
from wagtail.utils.deprecation import RemovedInWagtail70Warning


class ReportView(SpreadsheetExportMixin, PermissionCheckedMixin, BaseListingView):
    template_name = "wagtailadmin/reports/base_report.html"
    results_template_name = "wagtailadmin/reports/base_report_results.html"
    title = ""
    paginate_by = 50

    def get_page_title(self):
        if self.page_title:
            return self.page_title
        # WagtailAdminTemplateMixin uses `page_title`, but the documented approach
        # for ReportView used `title`, so we need to support both during the
        # deprecation period. When `title` is removed, this and the `get_context_data`
        # overrides can be removed.
        warn(
            f"The `title` attribute in `{self.__class__.__name__}` (a `ReportView` subclass) "
            "is deprecated. Use `page_title` instead.",
            RemovedInWagtail70Warning,
        )
        return self.title

    def get_filtered_queryset(self):
        return self.filter_queryset(self.get_queryset())

    def decorate_paginated_queryset(self, object_list):
        # A hook point to allow rewriting the object list after pagination has been applied
        return object_list

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_filtered_queryset()
        context = self.get_context_data()
        # Decorate the queryset *after* Django's BaseListView has returned a paginated/reduced
        # list of objects
        context["object_list"] = self.decorate_paginated_queryset(
            context["object_list"]
        )
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.get_page_title()
        return context

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
    permission_policy = page_permission_policy
