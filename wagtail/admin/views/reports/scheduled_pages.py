from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from wagtail.permissions import page_permission_policy

from .base import PageReportView


class ScheduledPagesView(PageReportView):
    """Report showing pages scheduled for future publish or unpublish"""

    results_template_name = "wagtailadmin/reports/scheduled_pages_results.html"
    page_title = _("Scheduled Pages")
    header_icon = "time"

    def get_filename(self):
        """Generate filename for XLSX export"""
        return "scheduled-pages-report-{}".format(datetime.today().strftime("%Y-%m-%d"))

    def get_queryset(self):
        pages = (
            page_permission_policy.instances_user_has_permission_for(
                self.request.user, "publish"
            )
            .annotate_approved_schedule()
            .filter(_approved_schedule=True)
            .prefetch_related("content_type")
            .order_by("-first_published_at")
        )
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not page_permission_policy.user_has_permission(request.user, "publish"):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
