import django_filters
from django import forms
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site


def get_redirect_pages_queryset(request) -> QuerySet[Page]:
    redirect_page_pks = (
        Redirect.objects.filter(redirect_page__isnull=False)
        .order_by()
        .values_list("redirect_page", flat=True)
        .distinct()
    )
    return Page.objects.filter(pk__in=redirect_page_pks)


class RedirectsReportFilterSet(WagtailFilterSet):
    redirect_page = django_filters.ModelChoiceFilter(
        field_name="redirect_page", queryset=get_redirect_pages_queryset
    )
    is_permanent = django_filters.ChoiceFilter(
        label=_("Type"),
        method="filter_type",
        choices=(
            (True, _("Permanent")),
            (False, _("Temporary")),
        ),
        empty_label=_("All"),
        widget=forms.RadioSelect,
    )

    site = django_filters.ModelChoiceFilter(
        field_name="site", queryset=Site.objects.all()
    )

    def filter_type(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(is_permanent=value)
        return queryset

    class Meta:
        model = Redirect
        exclude = []
