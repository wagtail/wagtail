import datetime

import django_filters
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.models import Page
from wagtail.permissions import page_permission_policy

from .base import PageReportView


def get_users_for_filter():
    User = get_user_model()
    return (
        User.objects.filter(locked_pages__isnull=False)
        .order_by(User.USERNAME_FIELD)
        .distinct()
    )


class LockedPagesReportFilterSet(WagtailFilterSet):
    locked_at = django_filters.DateFromToRangeFilter(widget=DateRangePickerWidget)
    locked_by = django_filters.ModelChoiceFilter(
        field_name="locked_by", queryset=lambda request: get_users_for_filter()
    )

    class Meta:
        model = Page
        fields = ["locked_by", "locked_at", "live"]


class LockedPagesView(PageReportView):
    results_template_name = "wagtailadmin/reports/locked_pages_results.html"
    page_title = _("Locked pages")
    header_icon = "lock"
    list_export = PageReportView.list_export + [
        "locked_at",
        "locked_by",
    ]
    filterset_class = LockedPagesReportFilterSet
    index_url_name = "wagtailadmin_reports:locked_pages"
    index_results_url_name = "wagtailadmin_reports:locked_pages_results"
    permission_required = "unlock"

    def get_filename(self):
        return "locked-pages-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = (
            (
                page_permission_policy.instances_user_has_permission_for(
                    self.request.user, "change"
                )
                | Page.objects.filter(locked_by=self.request.user)
            )
            .filter(locked=True)
            .specific(defer=True)
        )

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            pages = pages.select_related("locale")

        self.queryset = pages
        return super().get_queryset()
