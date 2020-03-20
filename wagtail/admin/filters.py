import django_filters
from django import forms
from django_filters.widgets import SuffixedMultiWidget

from wagtail.core.models import Page, WorkflowState, TaskState

from .widgets import AdminDateInput


class ButtonSelect(forms.Select):
    input_type = 'hidden'
    template_name = 'wagtailadmin/widgets/button_select.html'
    option_template_name = 'wagtailadmin/widgets/button_select_option.html'


class DateRangePickerWidget(SuffixedMultiWidget):
    template_name = 'wagtailadmin/widgets/daterange_input.html'
    suffixes = ['after', 'before']

    def __init__(self, attrs=None):
        widgets = (AdminDateInput(attrs={'placeholder': "Date from"}), AdminDateInput(attrs={'placeholder': "Date to"}))
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
            params.setdefault('empty_label', "All")

        elif filter_class in [django_filters.DateFilter, django_filters.DateTimeFilter]:
            params.setdefault('widget', AdminDateInput)

        elif filter_class == django_filters.DateFromToRangeFilter:
            params.setdefault('widget', DateRangePickerWidget)

        return filter_class, params


class LockedPagesReportFilterSet(WagtailFilterSet):
    locked_at = django_filters.DateFromToRangeFilter(widget=DateRangePickerWidget)

    class Meta:
        model = Page
        fields = ['locked_by', 'locked_at']


class WorkflowReportFilterSet(WagtailFilterSet):
    created_at = django_filters.DateFromToRangeFilter(label='Started at', widget=DateRangePickerWidget)

    class Meta:
        model = WorkflowState
        fields = ['workflow', 'status', 'created_at']


class WorkflowTasksReportFilterSet(WagtailFilterSet):
    created_at = django_filters.DateFromToRangeFilter(label='Started at', widget=DateRangePickerWidget)
    finished_at = django_filters.DateFromToRangeFilter(label='Completed at', widget=DateRangePickerWidget)

    class Meta:
        model = TaskState
        fields = ['task', 'status', 'created_at', 'finished_at']
