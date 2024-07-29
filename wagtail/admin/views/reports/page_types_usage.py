import django_filters
from django.conf import settings
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.coreutils import get_content_languages
from wagtail.models import ContentType, Page, Site, get_page_models
from wagtail.permissions import page_permission_policy


def _get_locale_choices():
    return list(get_content_languages().items())


def _get_site_choices():
    """Tuples of (site root page path, site display name) for all sites in project."""
    choices = [
        (site.root_page.path, str(site))
        for site in Site.objects.all().select_related("root_page")
    ]
    return choices


def _annotate_last_edit_info(queryset, language_code, site_root_path):
    latest_edited_page_filter_kwargs = {}
    page_count_filter_kwargs = {}
    if language_code:
        latest_edited_page_filter_kwargs["locale__language_code"] = language_code
        page_count_filter_kwargs["pages__locale__language_code"] = language_code
    if site_root_path:
        latest_edited_page_filter_kwargs["path__startswith"] = site_root_path
        page_count_filter_kwargs["pages__path__startswith"] = site_root_path

    latest_edited_page = Page.objects.filter(
        content_type=OuterRef("pk"), **latest_edited_page_filter_kwargs
    ).order_by(F("latest_revision_created_at").desc(nulls_last=True), "title", "-pk")

    queryset = queryset.annotate(
        count=Count("pages", filter=Q(**page_count_filter_kwargs)),
        last_edited_page_id=Subquery(latest_edited_page.values("pk")[:1]),
    )

    return queryset


class LocaleFilter(django_filters.ChoiceFilter):
    def filter(self, qs, language_code):
        if language_code:
            return qs.filter(pages__locale__language_code=language_code)
        return qs


class SiteFilter(django_filters.ChoiceFilter):
    def filter(self, qs, site_root_path):
        # Value passed will be the site root page path
        # To check if a page is in a site, we check if the page path starts with the
        # site's root page path
        if site_root_path:
            return qs.filter(pages__path__startswith=site_root_path)
        return qs


class PageTypesUsageReportFilterSet(WagtailFilterSet):
    page_locale = LocaleFilter(
        label=_("Locale"),
        choices=_get_locale_choices,
        empty_label=None,
        null_label=_("All"),
        null_value=None,
    )
    site = SiteFilter(
        label=_("Site"),
        choices=_get_site_choices,
        empty_label=None,
        null_label=_("All"),
        null_value=None,
    )

    class Meta:
        model = ContentType
        fields = ["page_locale", "site"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sites = {
            site.pk: site for site in Site.objects.all().prefetch_related("root_page")
        }
        self.sites_filter_enabled = True
        if len(self.sites) == 1:
            # If there is only one site, we don't need to show the site filter
            self.sites_filter_enabled = False
            del self.filters["site"]


class PageTypesUsageReportView(ReportView):
    results_template_name = "wagtailadmin/reports/page_types_usage_results.html"
    page_title = _("Page types usage")
    header_icon = "doc-empty-inverse"
    filterset_class = PageTypesUsageReportFilterSet
    index_url_name = "wagtailadmin_reports:page_types_usage"
    index_results_url_name = "wagtailadmin_reports:page_types_usage_results"
    permission_policy = page_permission_policy
    any_permission_required = ["add", "change", "publish"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page_models = [model.__name__.lower() for model in get_page_models()]
        self.i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)

    def decorate_paginated_queryset(self, page_types):
        pages_mapping = Page.objects.specific().in_bulk(
            obj.last_edited_page_id for obj in page_types if obj.last_edited_page_id
        )

        for item in page_types:
            item.last_edited_page = (
                pages_mapping[item.last_edited_page_id]
                if item.last_edited_page_id
                else None
            )

        return page_types

    def get_queryset(self):
        queryset = ContentType.objects.filter(model__in=self.page_models)

        page_content_type = ContentType.objects.get_for_model(Page)
        has_pages = Page.objects.filter(
            depth__gt=1, content_type=page_content_type
        ).exists()
        if not has_pages:
            # If there are no `wagtailcore.Page` pages, we don't need to
            # show it in the report
            queryset = queryset.exclude(id=page_content_type.id)

        self.queryset = queryset

        queryset = self.filter_queryset(queryset)

        language_code = self.filters.form.cleaned_data.get("page_locale", None)
        site_root_path = self.filters.form.cleaned_data.get("site", None)
        queryset = _annotate_last_edit_info(queryset, language_code, site_root_path)

        queryset = queryset.order_by("-count", "app_label", "model")

        return queryset
