from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.template import RequestContext
from django.template.loader import render_to_string

from wagtail.wagtailcore.models import Page, PageRevision, UserPagePermissionsProxy
from verdantimages.models import get_image_model
from wagtail.wagtaildocs.models import Document
from wagtail.wagtailadmin import hooks

# Panels for the homepage
class SiteSummaryPanel(object):
    name = 'site_summary'
    order = 100

    def __init__(self, request):
        self.request = request

    def render(self):
        return render_to_string('wagtailadmin/home/site_summary.html', {
            'total_pages': Page.objects.count() - 1,  # subtract 1 because the root node is not a real page
            'total_images': get_image_model().objects.count(),
            'total_docs': Document.objects.count(),
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
        self.last_edits = PageRevision.objects.filter(user=request.user).order_by('-created_at')[:5]

    def render(self):
        return render_to_string('wagtailadmin/home/recent_edits.html', {
            'last_edits': self.last_edits,
        }, RequestContext(self.request))

@login_required
def home(request):

    panels = [
        SiteSummaryPanel(request),
        PagesForModerationPanel(request),
        RecentEditsPanel(request),
    ]

    for fn in hooks.get_hooks('construct_homepage_panels'):
        fn(request, panels)

    return render(request, "wagtailadmin/home.html", {
        'site_name': settings.VERDANT_SITE_NAME,
        'panels': sorted(panels, key=lambda p: p.order),
        'user':request.user
    })


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")
