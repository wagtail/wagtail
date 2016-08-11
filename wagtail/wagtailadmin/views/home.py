from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db.models import F
from django.shortcuts import render
from django.template.loader import render_to_string

from wagtail.wagtailadmin.site_summary import SiteSummaryPanel
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import PageRevision, UserPagePermissionsProxy


# Panels for the homepage

class UpgradeNotificationPanel(object):
    name = 'upgrade_notification'
    order = 100

    def __init__(self, request):
        self.request = request

    def render(self):
        if self.request.user.is_superuser and getattr(settings, "WAGTAIL_ENABLE_UPDATE_CHECK", True):
            return render_to_string('wagtailadmin/home/upgrade_notification.html', {}, request=self.request)
        else:
            return ""


class PagesForModerationPanel(object):
    name = 'pages_for_moderation'
    order = 200

    def __init__(self, request):
        self.request = request
        user_perms = UserPagePermissionsProxy(request.user)
        self.page_revisions_for_moderation = (user_perms.revisions_for_moderation()
                                              .select_related('page', 'user').order_by('-created_at'))

    def render(self):
        return render_to_string('wagtailadmin/home/pages_for_moderation.html', {
            'page_revisions_for_moderation': self.page_revisions_for_moderation,
        }, request=self.request)


class RecentEditsPanel(object):
    name = 'recent_edits'
    order = 300

    def __init__(self, request):
        self.request = request
        # Last n edited pages
        self.last_edits = PageRevision.objects.filter(
            user=self.request.user,
            created_at=F('page__latest_revision_created_at')
        ).order_by('-created_at')[:5]

    def render(self):
        return render_to_string('wagtailadmin/home/recent_edits.html', {
            'last_edits': self.last_edits,
        }, request=self.request)


def home(request):

    panels = [
        SiteSummaryPanel(request),
        UpgradeNotificationPanel(request),
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
