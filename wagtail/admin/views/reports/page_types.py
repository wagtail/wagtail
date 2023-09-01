import django_filters
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Q, Subquery
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.coreutils import get_content_languages
from wagtail.models import ContentType, Page, PageLogEntry, get_page_models
from wagtail.users.utils import get_deleted_user_display_name


def _get_locale_choices():
    choices = [
        (language_code, display_name)
        for language_code, display_name in get_content_languages().items()
    ]
    return choices


class LocaleFilter(django_filters.ChoiceFilter):
    def filter(self, qs, value):
        if value and value != self.null_value:
            latest_edit_log = PageLogEntry.objects.filter(
                content_type=OuterRef("pk"), page__locale__language_code=value
            )
            count_qs = Count("pages", filter=Q(pages__locale__language_code=value))
        else:
            latest_edit_log = PageLogEntry.objects.filter(content_type=OuterRef("pk"))
            count_qs = Count("pages")

        latest_edit_log = latest_edit_log.order_by("-timestamp", "-pk")

        qs = qs.annotate(
            count=count_qs,
            last_edited_page=Subquery(latest_edit_log.values("page")[:1]),
            last_edited_by=Subquery(latest_edit_log.values("user")[:1]),
        )

        return qs


class PageTypesReportFilterSet(WagtailFilterSet):
    page_locale = LocaleFilter(
        label=_("Locale"),
        choices=_get_locale_choices,
        empty_label=None,
        null_label=_("All"),
        null_value="all",
    )

    class Meta:
        model = ContentType
        fields = ["page_locale"]


class PageTypesReportView(ReportView):
    template_name = "wagtailadmin/reports/page_types.html"
    title = _("Page types")
    header_icon = "doc-empty-inverse"
    filterset_class = PageTypesReportFilterSet

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_model = get_user_model()
        self.page_models = [model.__name__.lower() for model in get_page_models()]

    def user_id_to_python(self, user_id):
        return self.user_model._meta.pk.to_python(user_id)

    def add_last_edited_name_to_page_type(self, username_mapping, page_type):
        if page_type.last_edited_by:
            # Giving the last_published_by annotation an explicit output_field type
            # causes an issue with prefetch_workflow_states when the field is a
            # ConvertedValueField. If the last user to publish the page has been
            # deleted, we will render their user id in the template, so we call
            # to_python on the value so that what's rendered matches the developer's
            # expectation in the case of complex primary key types (e.g. UUIDField).
            try:
                user_id_value = self.user_id_to_python(page_type.last_edited_by)
            except ValidationError:
                user_id_value = page_type.last_edited_by

            last_edited_by_user = username_mapping.get(
                user_id_value, get_deleted_user_display_name(user_id=user_id_value)
            )
            page_type.last_edited_by_user = last_edited_by_user

    def add_last_edited_page_to_page_type(self, pages_mapping, page_type):
        if page_type.last_edited_page:
            last_edited_page = pages_mapping.get(page_type.last_edited_page, None)
            page_type.last_edited_page = last_edited_page

    def decorate_paginated_queryset(self, page_types):
        page_ids = set(page_types.values_list("last_edited_page", flat=True))
        pages_mapping = {page.pk: page for page in Page.objects.filter(pk__in=page_ids)}

        user_ids = set(page_types.values_list("last_edited_by", flat=True))
        username_mapping = {
            user.pk: user.get_username()
            for user in self.user_model.objects.filter(pk__in=user_ids)
        }

        for page_type in page_types:
            self.add_last_edited_page_to_page_type(pages_mapping, page_type)
            self.add_last_edited_name_to_page_type(username_mapping, page_type)
        return page_types

    def get_queryset(self):
        queryset = ContentType.objects.filter(model__in=self.page_models)
        self.queryset = queryset

        self.filters, queryset = self.filter_queryset(queryset)

        # 'updated_at' is handled at the filter level, since ContentType itself does not
        # have a locale to filter on

        queryset = queryset.order_by("-count", "app_label", "model")

        return queryset
