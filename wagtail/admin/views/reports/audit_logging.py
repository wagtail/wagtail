import datetime

import django_filters

from django import forms
from django.db.models import Q, Subquery
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.core.log_actions import page_log_action_registry
from wagtail.core.models import Page, PageLogEntry, UserPagePermissionsProxy

from .base import ReportView


class SiteHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(choices=page_log_action_registry.get_choices)
    hide_commenting_actions = django_filters.BooleanFilter(
        label=_('Hide commenting actions'),
        method='filter_hide_commenting_actions',
        widget=forms.CheckboxInput,
    )
    timestamp = django_filters.DateFromToRangeFilter(label=_('Date'), widget=DateRangePickerWidget)
    label = django_filters.CharFilter(label=_('Title'), lookup_expr='icontains')
    user = django_filters.ModelChoiceFilter(
        field_name='user', queryset=lambda request: PageLogEntry.objects.all().get_users()
    )

    def filter_hide_commenting_actions(self, queryset, name, value):
        if value:
            queryset = queryset.exclude(
                action__startswith='wagtail.comments'
            )
        return queryset

    class Meta:
        model = PageLogEntry
        fields = ['label', 'action', 'user', 'timestamp', 'hide_commenting_actions']


class LogEntriesView(ReportView):
    template_name = 'wagtailadmin/reports/site_history.html'
    title = _('Site history')
    header_icon = 'history'
    filterset_class = SiteHistoryReportFilterSet

    export_headings = {
        "object_id": _("ID"),
        "title": _("Title"),
        "object_verbose_name": _("Type"),
        "action": _("Action type"),
        "timestamp": _("Date/Time")
    }
    list_export = [
        "object_id",
        "label",
        "object_verbose_name",
        "action",
        "timestamp"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.custom_field_preprocess['action'] = {
            self.FORMAT_CSV: self.get_action_label,
            self.FORMAT_XLSX: self.get_action_label
        }

    def get_filename(self):
        return "audit-log-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        q = Q(page__in=UserPagePermissionsProxy(self.request.user).explorable_pages())

        root_page_permissions = Page.get_first_root_node().permissions_for_user(self.request.user)
        if (
            self.request.user.is_superuser
            or root_page_permissions.can_add_subpage() or root_page_permissions.can_edit()
        ):
            # Include deleted entries
            q = q | Q(page_id__in=Subquery(
                PageLogEntry.objects.filter(deleted=True).values('page_id')
            ))

        # Using prefech_related() on page, as select_related() generates an INNER JOIN,
        # which filters out entries for deleted pages
        return PageLogEntry.objects.filter(q).select_related(
            'user', 'user__wagtail_userprofile'
        ).prefetch_related('page')

    def get_action_label(self, action):
        from wagtail.core.log_actions import page_log_action_registry
        return force_str(page_log_action_registry.get_action_label(action))
