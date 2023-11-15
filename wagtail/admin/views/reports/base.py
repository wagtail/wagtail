from django.utils.translation import gettext_lazy as _

from wagtail.admin.views.generic.models import IndexView


class ReportView(IndexView):
    template_name = "wagtailadmin/reports/base_report.html"
    title = ""
    paginate_by = 50

    def get_filtered_queryset(self):
        return self.filter_queryset(self.get_queryset())

    def decorate_paginated_queryset(self, object_list):
        # A hook point to allow rewriting the object list after pagination has been applied
        return object_list

    def get(self, request, *args, **kwargs):
        self.filters, self.object_list = self.get_filtered_queryset()
        context = self.get_context_data()
        # Decorate the queryset *after* Django's BaseListView has returned a paginated/reduced
        # list of objects
        context["object_list"] = self.decorate_paginated_queryset(
            context["object_list"]
        )
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.title
        return context


class PageReportView(ReportView):
    template_name = "wagtailadmin/reports/base_page_report.html"
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
