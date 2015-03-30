from django.shortcuts import render
from django.conf import settings
from django.template import RequestContext
from django.template.loader import render_to_string

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page, PageRevision, UserPagePermissionsProxy

from wagtail.wagtaildocs.models import Document

from wagtail.wagtailimages.models import get_image_model


# Items for the site summary panel
class SummaryItem(object):
    order = 100

    def __init__(self, request):
        self.request = request

    def get_context(self):
        return {}

    def render(self):
        return render_to_string(self.template, self.get_context(),
            RequestContext(self.request))


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


class ImagesSummaryItem(SummaryItem):
    order = 200
    template = 'wagtailadmin/home/site_summary_images.html'

    def get_context(self):
        return {
            'total_images': get_image_model().objects.count(),
        }

@hooks.register('construct_homepage_summary_items')
def add_images_summary_item(request, items):
    items.append(ImagesSummaryItem(request))


class DocumentsSummaryItem(SummaryItem):
    order = 300
    template = 'wagtailadmin/home/site_summary_documents.html'

    def get_context(self):
        return {
            'total_docs': Document.objects.count(),
        }

@hooks.register('construct_homepage_summary_items')
def add_documents_summary_item(request, items):
    items.append(DocumentsSummaryItem(request))


# Panels for the homepage
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
        }, RequestContext(self.request))


class PagesForModerationPanel(object):
    name = 'pages_for_moderation'
    order = 200

    def __init__(self, request):
        self.request = request
        user_perms = UserPagePermissionsProxy(request.user)
        self.page_revisions_for_moderation = user_perms.revisions_for_moderation().select_related('page', 'user').order_by('-created_at')

    def render(self):
        return render_to_string('wagtailadmin/home/pages_for_moderation.html', {
            'page_revisions_for_moderation': self.page_revisions_for_moderation,
        }, RequestContext(self.request))


class RecentEditsPanel(object):
    name = 'recent_edits'
    order = 300

    def __init__(self, request):
        self.request = request
        # Last n edited pages
        self.last_edits = PageRevision.objects.raw(
            """
            select wp.* FROM
                wagtailcore_pagerevision wp JOIN (
                    SELECT max(created_at) as max_created_at, page_id FROM wagtailcore_pagerevision group by page_id 
                ) as max_rev on max_rev.max_created_at = wp.created_at and wp.user_id = %s order by wp.created_at desc
            """, [request.user.id])[:5]
    def render(self):
        return render_to_string('wagtailadmin/home/recent_edits.html', {
            'last_edits': self.last_edits,
        }, RequestContext(self.request))


def home(request):

    panels = [
        SiteSummaryPanel(request),
        PagesForModerationPanel(request),
        RecentEditsPanel(request),
    ]

    for fn in hooks.get_hooks('construct_homepage_panels'):
        fn(request, panels)

    return render(request, "wagtailadmin/home.html", {
        'site_name': settings.WAGTAIL_SITE_NAME,
        'panels': sorted(panels, key=lambda p: p.order),
        'user': request.user
    })


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")
