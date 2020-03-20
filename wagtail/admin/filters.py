import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _
from django_filters.widgets import SuffixedMultiWidget

from wagtail.core.models import Page

from .widgets import AdminDateInput


class ButtonSelect(forms.Select):
    """
    A select widget for fields with choices. Displays as a list of buttons.
    """
    input_type = 'hidden'
    template_name = 'wagtailadmin/widgets/button_select.html'
    option_template_name = 'wagtailadmin/widgets/button_select_option.html'


class BooleanButtonSelect(ButtonSelect):
    """
    A select widget for boolean fields. Displays as three buttons. "All", "Yes" and "No".
    """
    def __init__(self, attrs=None):
        choices = (
            ('', _("All")),
            ('true', _("Yes")),
            ('false', _("No")),
        )
        super().__init__(attrs, choices)

    def format_value(self, value):
        try:
            return {
                True: ['true'], False: ['false'],
                'true': ['true'], 'false': ['false'],
            }[value]
        except KeyError:
            return ''

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return {
            True: True,
            'True': True,
            'False': False,
            False: False,
            'true': True,
            'false': False,
        }.get(value)


class DateRangePickerWidget(SuffixedMultiWidget):
    """
    A widget allowing a start and end date to be picked.
    """
    template_name = 'wagtailadmin/widgets/daterange_input.html'
    suffixes = ['after', 'before']

    def __init__(self, attrs=None):
        widgets = (AdminDateInput(attrs={'placeholder': _("Date from")}), AdminDateInput(attrs={'placeholder': _("Date to")}))
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class WagtailFilterSet(django_filters.FilterSet):

    @classmethod
    def filter_for_lookup(cls, field, lookup_type):
        filter_class, params = super().filter_for_lookup(field, lookup_type)

        if filter_class == django_filters.ChoiceFilter:
            params.setdefault('widget', ButtonSelect)
            params.setdefault('empty_label', _("All"))

        elif filter_class in [django_filters.DateFilter, django_filters.DateTimeFilter]:
            params.setdefault('widget', AdminDateInput)

        elif filter_class == django_filters.DateFromToRangeFilter:
            params.setdefault('widget', DateRangePickerWidget)

        elif filter_class == django_filters.BooleanFilter:
            params.setdefault('widget', BooleanButtonSelect)

        return filter_class, params


class LockedPagesReportFilterSet(WagtailFilterSet):
    locked_at = django_filters.DateFromToRangeFilter(widget=DateRangePickerWidget)

    class Meta:
        model = Page
        fields = ['locked_by', 'locked_at', 'live']
