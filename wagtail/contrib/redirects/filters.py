import django_filters
from django import forms
from django.utils.translation import gettext as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site


class RedirectsReportFilterSet(WagtailFilterSet):
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
        fields = ["is_permanent", "site"]
