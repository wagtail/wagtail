import datetime

import django_filters

from django.contrib.auth import get_user_model
from django.db.models import Q, Subquery
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.core.log_actions import page_log_action_registry
from wagtail.core.models import Page, PageLogEntry, UserPagePermissionsProxy

from .base import ReportView


def get_audit_log_users_queryset(request):
    User = get_user_model()
    return User.objects.filter(
        pk__in=set(PageLogEntry.objects.values_list('user__pk', flat=True))
    ).order_by(User.USERNAME_FIELD)


class SiteHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(choices=page_log_action_registry.get_choices)
    timestamp = django_filters.DateFromToRangeFilter(label=_('Date'), widget=DateRangePickerWidget)
    label = django_filters.CharFilter(label=_('Title'), lookup_expr='icontains')
    user = django_filters.ModelChoiceFilter(
        field_name='user', queryset=get_audit_log_users_queryset
    )

    class Meta:
        model = PageLogEntry
        fields = ['label', 'action', 'user', 'timestamp']


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
        q = Q(
            page__in=UserPagePermissionsProxy(self.request.user).explorable_pages().values_list('pk', flat=True)
        )

        root_page_permissions = Page.get_first_root_node().permissions_for_user(self.request.user)
        if (
            self.request.user.is_superuser
            or root_page_permissions.can_add_subpage() or root_page_permissions.can_edit()
        ):
            # Include deleted entries
            q = q | Q(page_id__in=Subquery(
                PageLogEntry.objects.filter(deleted=True).values('page_id')
            ))

        return PageLogEntry.objects.filter(q)

    def get_action_label(self, action):
        from wagtail.core.log_actions import page_log_action_registry
        return force_str(page_log_action_registry.get_action_label(action))
