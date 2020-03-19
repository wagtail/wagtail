import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.core.models import Page


class ButtonSelect(forms.Select):
    input_type = 'hidden'
    template_name = 'wagtailadmin/widgets/button_select.html'
    option_template_name = 'wagtailadmin/widgets/button_select_option.html'


class WagtailFilterSet(django_filters.FilterSet):

    @classmethod
    def filter_for_lookup(cls, field, lookup_type):
        filter_class, params = super().filter_for_lookup(field, lookup_type)

        if filter_class == django_filters.ChoiceFilter:
            params.setdefault('widget', ButtonSelect)
            params.setdefault('empty_label', _("All"))

        return filter_class, params


class LockedPagesReportFilterSet(WagtailFilterSet):

    class Meta:
        model = Page
        fields = ['title', 'locked_by', 'locked_at']
