from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin.auth import permission_denied
from wagtail.core.models import UserPagePermissionsProxy


class ReportView(TemplateResponseMixin, BaseListView):
    header_icon = ''
    page_kwarg = 'p'
    template_name = None
    title = ''
    paginate_by = 10

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context['title'] = self.title
        context['header_icon'] = self.header_icon
        return context


class LockedPagesView(ReportView):
    template_name = 'wagtailadmin/reports/locked_pages.html'
    title = _('Locked Pages')
    header_icon = 'locked'

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages().filter(locked=True)
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_remove_locks():
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
