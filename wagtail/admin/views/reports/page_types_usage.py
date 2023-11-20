import django_filters
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.coreutils import get_content_languages
from wagtail.models import ContentType, Page, Site, get_page_models
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.users.utils import get_deleted_user_display_name


def _get_locale_choices():
    choices = [  # noqa: C416
        (language_code, display_name)
        for language_code, display_name in get_content_languages().items()
    ]
    return choices


def _get_site_choices():
    """Tuples of (site root page path, site display name) for all sites in project."""
    choices = [(site.root_page.path, str(site)) for site in Site.objects.all()]
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
        last_edited_page_owner_id=Subquery(latest_edited_page.values("owner__pk")[:1]),
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
    template_name = "wagtailadmin/reports/page_types_usage.html"
    title = _("Page types usage")
    header_icon = "doc-empty-inverse"
    filterset_class = PageTypesUsageReportFilterSet

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_model = get_user_model()
        self.page_models = [model.__name__.lower() for model in get_page_models()]
        self.i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)

    def user_id_to_python(self, user_id):
        return self.user_model._meta.pk.to_python(user_id)

    def add_last_edited_name_to_page_type(self, username_mapping, page_type):
        if page_type.last_edited_page_owner_id:
            # Giving the last_published_by annotation an explicit output_field type
            # causes an issue with prefetch_workflow_states when the field is a
            # ConvertedValueField. If the last user to publish the page has been
            # deleted, we will render their user id in the template, so we call
            # to_python on the value so that what's rendered matches the developer's
            # expectation in the case of complex primary key types (e.g. UUIDField).
            try:
                user_id_value = self.user_id_to_python(
                    page_type.last_edited_page_owner_id
                )
            except ValidationError:
                user_id_value = page_type.last_edited_page_owner_id

            last_edited_page_owner = username_mapping.get(
                user_id_value, get_deleted_user_display_name(user_id=user_id_value)
            )
            page_type.last_edited_page_owner = last_edited_page_owner

    def add_last_edited_page_to_page_type(self, pages_mapping, page_type):
        if page_type.last_edited_page_id:
            last_edited_page = pages_mapping.get(page_type.last_edited_page_id, None)
            page_type.last_edited_page = last_edited_page

    def decorate_paginated_queryset(self, page_types):
        page_ids = set(page_types.values_list("last_edited_page_id", flat=True))
        pages = Page.objects.filter(pk__in=page_ids).select_related("owner")

        pages_mapping = {page.pk: page for page in pages}
        username_mapping = {
            page.owner.pk: page.owner.get_username() for page in pages if page.owner
        }

        for page_type in page_types:
            self.add_last_edited_page_to_page_type(pages_mapping, page_type)
            self.add_last_edited_name_to_page_type(username_mapping, page_type)
        return page_types

    def get_queryset(self):
        queryset = ContentType.objects.filter(model__in=self.page_models)
        self.queryset = queryset

        self.filters, queryset = self.filter_queryset(queryset)

        language_code = self.filters.form.cleaned_data.get("page_locale", None)
        site_root_path = self.filters.form.cleaned_data.get("site", None)
        queryset = _annotate_last_edit_info(queryset, language_code, site_root_path)

        queryset = queryset.order_by("-count", "app_label", "model")

        return queryset

    def dispatch(self, request, *args, **kwargs):
        if not PagePermissionPolicy().user_has_any_permission(
            request.user, ["add", "change", "publish"]
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
