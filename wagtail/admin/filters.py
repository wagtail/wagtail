import django_filters

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_filters.widgets import SuffixedMultiWidget

from wagtail.admin.log_action_registry import registry as log_action_registry
from wagtail.admin.widgets import AdminDateInput, BooleanButtonSelect, ButtonSelect, FilteredSelect
from wagtail.core.models import Page, PageLogEntry, Task, TaskState, Workflow, WorkflowState


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


class FilteredModelChoiceIterator(django_filters.fields.ModelChoiceIterator):
    """
    A variant of Django's ModelChoiceIterator that, instead of yielding (value, label) tuples,
    returns (value, label, filter_value) so that FilteredSelect can drop filter_value into
    the data-filter-value attribute.
    """
    def choice(self, obj):
        return (
            self.field.prepare_value(obj),
            self.field.label_from_instance(obj),
            self.field.get_filter_value(obj)
        )


class FilteredModelChoiceField(django_filters.fields.ModelChoiceField):
    """
    A ModelChoiceField that uses FilteredSelect to dynamically show/hide options based on another
    ModelChoiceField of related objects; an option will be shown whenever the selected related
    object is present in the result of filter_accessor for that option.

    filter_field - the HTML `id` of the related ModelChoiceField
    filter_accessor - either the name of a relation, property or method on the model instance which
        returns a queryset of related objects, or a function which accepts the model instance and
        returns such a queryset.
    """
    widget = FilteredSelect
    iterator = FilteredModelChoiceIterator

    def __init__(self, *args, **kwargs):
        self.filter_accessor = kwargs.pop('filter_accessor')
        filter_field = kwargs.pop('filter_field')
        super().__init__(*args, **kwargs)
        self.widget.filter_field = filter_field

    def get_filter_value(self, obj):
        # Use filter_accessor to obtain a queryset of related objects
        if callable(self.filter_accessor):
            queryset = self.filter_accessor(obj)
        else:
            # treat filter_accessor as a method/property name of obj
            queryset = getattr(obj, self.filter_accessor)
            if isinstance(queryset, models.Manager):
                queryset = queryset.all()
            elif callable(queryset):
                queryset = queryset()

        # Turn this queryset into a list of IDs that will become the 'data-filter-value' used to
        # filter this listing
        return queryset.values_list('pk', flat=True)


class FilteredModelChoiceFilter(django_filters.ModelChoiceFilter):
    field_class = FilteredModelChoiceField


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


def get_requested_by_queryset(request):
    User = get_user_model()
    return User.objects.filter(
        pk__in=set(WorkflowState.objects.values_list('requested_by__pk', flat=True))
    ).order_by(User.USERNAME_FIELD)


class WorkflowReportFilterSet(WagtailFilterSet):
    created_at = django_filters.DateFromToRangeFilter(label=_("Started at"), widget=DateRangePickerWidget)
    reviewable = django_filters.ChoiceFilter(
        label=_("Show"),
        method='filter_reviewable',
        choices=(
            ('true', _("Awaiting my review")),
        ),
        empty_label=_("All"),
        widget=ButtonSelect
    )
    requested_by = django_filters.ModelChoiceFilter(
        field_name='requested_by', queryset=get_requested_by_queryset
    )

    def filter_reviewable(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(current_task_state__in=TaskState.objects.reviewable_by(self.request.user))
        return queryset

    class Meta:
        model = WorkflowState
        fields = ['reviewable', 'workflow', 'status', 'requested_by', 'created_at']


class WorkflowTasksReportFilterSet(WagtailFilterSet):
    started_at = django_filters.DateFromToRangeFilter(label=_("Started at"), widget=DateRangePickerWidget)
    finished_at = django_filters.DateFromToRangeFilter(label=_("Completed at"), widget=DateRangePickerWidget)
    workflow = django_filters.ModelChoiceFilter(
        field_name='workflow_state__workflow', queryset=Workflow.objects.all(), label=_("Workflow")
    )

    # When a workflow is chosen in the 'id_workflow' selector, filter this list of tasks
    # to just the ones whose workflows attribute includes the selected workflow.
    task = FilteredModelChoiceFilter(
        queryset=Task.objects.all(), filter_field='id_workflow', filter_accessor='workflows'
    )

    reviewable = django_filters.ChoiceFilter(
        label=_("Show"),
        method='filter_reviewable',
        choices=(
            ('true', _("Awaiting my review")),
        ),
        empty_label=_("All"),
        widget=ButtonSelect
    )

    def filter_reviewable(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(id__in=TaskState.objects.reviewable_by(self.request.user).values_list('id', flat=True))
        return queryset

    class Meta:
        model = TaskState
        fields = ['reviewable', 'workflow', 'task', 'status', 'started_at', 'finished_at']


def get_audit_log_users_queryset(request):
    User = get_user_model()
    return User.objects.filter(
        pk__in=set(PageLogEntry.objects.values_list('user__pk', flat=True))
    ).order_by(User.USERNAME_FIELD)


class SiteHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(choices=log_action_registry.get_choices)
    timestamp = django_filters.DateFromToRangeFilter(label=_('Date'), widget=DateRangePickerWidget)
    label = django_filters.CharFilter(label=_('Title'), lookup_expr='icontains')
    user = django_filters.ModelChoiceFilter(
        field_name='user', queryset=get_audit_log_users_queryset
    )

    class Meta:
        model = PageLogEntry
        fields = ['label', 'action', 'user', 'timestamp']


class PageHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(choices=log_action_registry.get_choices)
    user = django_filters.ModelChoiceFilter(
        field_name='user', queryset=get_audit_log_users_queryset
    )
    timestamp = django_filters.DateFromToRangeFilter(label=_('Date'), widget=DateRangePickerWidget)

    class Meta:
        model = PageLogEntry
        fields = ['action', 'user', 'timestamp']
