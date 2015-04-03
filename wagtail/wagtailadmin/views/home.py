from django.shortcuts import render
from django.conf import settings
from django.template import RequestContext
from django.template.loader import render_to_string

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import PageRevision, UserPagePermissionsProxy

from wagtail.wagtailadmin.site_summary import SiteSummaryPanel


# Panels for the homepage
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
