from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page
from wagtail.utils.compat import render_to_string


class SummaryItem(object):
    order = 100

    def __init__(self, request):
        self.request = request

    def get_context(self):
        return {}

    def render(self):
        return render_to_string(self.template, self.get_context(), request=self.request)


class PagesSummaryItem(SummaryItem):
    order = 100
    template = 'wagtailadmin/home/site_summary_pages.html'

    def get_context(self):
        return {
            'total_pages': Page.objects.count() - 1,  # subtract 1 because the root node is not a real page
        }

@hooks.register('construct_homepage_summary_items')
def add_pages_summary_item(request, items):
    items.append(PagesSummaryItem(request))


class SiteSummaryPanel(object):
    name = 'site_summary'
    order = 100

    def __init__(self, request):
        self.request = request
        self.summary_items = []
        for fn in hooks.get_hooks('construct_homepage_summary_items'):
            fn(request, self.summary_items)

    def render(self):
        return render_to_string('wagtailadmin/home/site_summary.html', {
            'summary_items': sorted(self.summary_items, key=lambda p: p.order),
        }, request=self.request)
