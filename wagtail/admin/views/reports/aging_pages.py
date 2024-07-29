import django_filters
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Subquery
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import ContentTypeFilter, WagtailFilterSet
from wagtail.admin.widgets import AdminDateInput
from wagtail.coreutils import get_content_type_label
from wagtail.models import Page, PageLogEntry, get_page_content_types
from wagtail.permissions import page_permission_policy
from wagtail.users.utils import get_deleted_user_display_name

from .base import PageReportView


class AgingPagesReportFilterSet(WagtailFilterSet):
    last_published_at = django_filters.DateTimeFilter(
        label=_("Last published before"), lookup_expr="lte", widget=AdminDateInput
    )
    content_type = ContentTypeFilter(
        label=_("Type"),
        queryset=lambda request: get_page_content_types(include_base_page_type=False),
    )

    class Meta:
        model = Page
        fields = ["live", "last_published_at", "content_type"]


class AgingPagesView(PageReportView):
    results_template_name = "wagtailadmin/reports/aging_pages_results.html"
    page_title = _("Aging pages")
    header_icon = "time"
    filterset_class = AgingPagesReportFilterSet
    index_url_name = "wagtailadmin_reports:aging_pages"
    index_results_url_name = "wagtailadmin_reports:aging_pages_results"
    export_headings = {
        "status_string": _("Status"),
        "last_published_at": _("Last published at"),
        "last_published_by_user": _("Last published by"),
        "content_type": _("Type"),
    }
    list_export = [
        "title",
        "status_string",
        "last_published_at",
        "last_published_by_user",
        "content_type",
    ]
    any_permission_required = ["add", "change", "publish"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.user_model = get_user_model()
        self.custom_field_preprocess = self.custom_field_preprocess.copy()
        self.custom_field_preprocess["content_type"] = {
            self.FORMAT_CSV: get_content_type_label,
            self.FORMAT_XLSX: get_content_type_label,
        }

    def user_id_to_python(self, user_id):
        return self.user_model._meta.pk.to_python(user_id)

    def add_last_publisher_name_to_page(self, username_mapping, page):
        if page.last_published_by:
            # Giving the last_published_by annotation an explicit output_field type
            # causes an issue with prefetch_workflow_states when the field is a
            # ConvertedValueField. If the last user to publish the page has been
            # deleted, we will render their user id in the template, so we call
            # to_python on the value so that what's rendered matches the developer's
            # expectation in the case of complex primary key types (e.g. UUIDField).
            try:
                user_id_value = self.user_id_to_python(page.last_published_by)
            except ValidationError:
                user_id_value = page.last_published_by

            last_published_by_user = username_mapping.get(
                user_id_value, get_deleted_user_display_name(user_id=user_id_value)
            )
            page.last_published_by_user = last_published_by_user
        else:
            page.last_published_by_user = ""

    def decorate_paginated_queryset(self, queryset):
        user_ids = set(queryset.values_list("last_published_by", flat=True))

        username_mapping = {
            user.pk: user.get_username()
            for user in self.user_model.objects.filter(pk__in=user_ids)
        }
        for page in queryset:
            self.add_last_publisher_name_to_page(username_mapping, page)
        return queryset

    def get_queryset(self):
        latest_publishing_log = PageLogEntry.objects.filter(
            page=OuterRef("pk"), action__exact="wagtail.publish"
        )
        self.queryset = (
            page_permission_policy.instances_user_has_permission_for(
                self.request.user, "publish"
            )
            .exclude(last_published_at__isnull=True)
            .prefetch_workflow_states()
            .select_related("content_type")
            .annotate_approved_schedule()
            .order_by("last_published_at")
            .annotate(
                last_published_by=Subquery(latest_publishing_log.values("user")[:1])
            )
        )

        return super().get_queryset()
