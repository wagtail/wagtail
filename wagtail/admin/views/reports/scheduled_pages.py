from datetime import datetime

import django_filters
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.views.reports.base import PageReportView
from wagtail.admin.views.scheduled_pages import get_scheduled_pages_for_user
from wagtail.core.models import Page, UserPagePermissionsProxy


class ScheduledPagesReportFilterSet(WagtailFilterSet):
    go_live_at = django_filters.DateFromToRangeFilter(widget=DateRangePickerWidget)

    class Meta:
        model = Page
        fields = ["go_live_at"]


class ScheduledPagesView(PageReportView):
    template_name = "wagtailadmin/reports/scheduled_pages.html"
    title = _("Pages scheduled for publishing")
    header_icon = "time"
    list_export = PageReportView.list_export
    filterset_class = ScheduledPagesReportFilterSet

    def get_filename(self):
        return "scheduled-pages-report-{}".format(datetime.today().strftime("%Y-%m-%d"))

    def get_queryset(self):
        self.queryset = get_scheduled_pages_for_user(self.request)
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_publish_pages():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
