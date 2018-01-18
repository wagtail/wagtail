from django.template.loader import render_to_string

from wagtail.admin.navigation import get_explorable_root_page
from wagtail.admin.utils import user_has_any_page_permission
from wagtail.core import hooks
from wagtail.core.models import Page


class SummaryItem:
    order = 100

    def __init__(self, request):
        self.request = request

    def get_context(self):
        return {}

    def render(self):
        return render_to_string(self.template, self.get_context(), request=self.request)

    def is_shown(self):
        return True


class PagesSummaryItem(SummaryItem):
    order = 100
    template = 'wagtailadmin/home/site_summary_pages.html'

    def get_context(self):
        root_page = get_explorable_root_page(self.request.user)

        if root_page:
            pages = Page.objects.descendant_of(root_page, inclusive=True)

            # If the root page the user has access to is the Wagtail root,
            # subtract one from this count because the root is not a real page.
            page_count = pages.count() - int(root_page.is_root())
        else:
            page_count = 0

        return {
            'root_page': root_page,
            'total_pages': page_count,
        }

    def is_shown(self):
        return user_has_any_page_permission(self.request.user)


@hooks.register('construct_homepage_summary_items')
def add_pages_summary_item(request, items):
    items.append(PagesSummaryItem(request))


class SiteSummaryPanel:
    name = 'site_summary'
    order = 100

    def __init__(self, request):
        self.request = request
        self.summary_items = []
        for fn in hooks.get_hooks('construct_homepage_summary_items'):
            fn(request, self.summary_items)

    def render(self):
        summary_items = [s for s in self.summary_items if s.is_shown()]
        if not summary_items:
            return ''

        return render_to_string('wagtailadmin/home/site_summary.html', {
            'summary_items': sorted(summary_items, key=lambda p: p.order),
        }, request=self.request)
