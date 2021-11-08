import django_filters

from django.db.models import OuterRef, Subquery
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.widgets import AdminDateInput
from wagtail.core.models import Page, PageLogEntry, UserPagePermissionsProxy

from .base import PageReportView


class AgingPagesReportFilterSet(WagtailFilterSet):
    last_published_at = django_filters.DateTimeFilter(
        label=_("Last published before"), lookup_expr="lte", widget=AdminDateInput
    )

    class Meta:
        model = Page
        fields = ["live", "last_published_at", "content_type"]


class AgingPagesView(PageReportView):
    template_name = "wagtailadmin/reports/aging_pages.html"
    title = _("Aging pages")
    filterset_class = AgingPagesReportFilterSet
    export_headings = {
        "status_string": _("Status"),
        "last_published_at": _("Last published at"),
        "last_published_by": _("Last published by"),
        "content_type.model_class._meta.verbose_name.title": _("Type"),
    }
    list_export = [
        "title",
        "status_string",
        "last_published_at",
        "last_published_by",
        "content_type.model_class._meta.verbose_name.title",
    ]

    def get_queryset(self):
        latest_publishing_log = PageLogEntry.objects.filter(
            page=OuterRef("pk"), action__exact="wagtail.publish"
        )
        pages = (
            UserPagePermissionsProxy(self.request.user)
            .publishable_pages()
            .exclude(last_published_at__isnull=True)
            .annotate(
                last_published_by=Subquery(
                    latest_publishing_log.values("user__username")[:1]
                )
            )
        )
        return pages
