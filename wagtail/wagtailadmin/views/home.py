from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections
from django.shortcuts import render
from django.template.loader import render_to_string

from wagtail.wagtailadmin.navigation import get_explorable_root_page
from wagtail.wagtailadmin.site_summary import SiteSummaryPanel
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page, PageRevision, UserPagePermissionsProxy


User = get_user_model()
pk_field_name = User._meta.pk.name
pk_field = User._meta.get_field(pk_field_name)


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
        last_edits = PageRevision.objects.raw(
            """
            SELECT wp.* FROM
                wagtailcore_pagerevision wp JOIN (
                    SELECT max(created_at) AS max_created_at, page_id FROM
                        wagtailcore_pagerevision WHERE %s = %s GROUP BY page_id ORDER BY max_created_at DESC LIMIT %s
                ) AS max_rev ON max_rev.max_created_at = wp.created_at ORDER BY wp.created_at DESC
             """, [
                    User._meta.pk.column,
                    pk_field.get_db_prep_value(self.request.user.pk, connections['default']),
                    5,
        ])
        last_edits = list(last_edits)
        page_keys = [pr.page.pk for pr in last_edits]
        specific_pages = Page.objects.filter(pk__in=page_keys).specific()
        pages = {p.pk: p for p in specific_pages}
        self.last_edits = [
            [review, pages.get(review.page.pk)] for review in last_edits
        ]

    def render(self):
        return render_to_string('wagtailadmin/home/recent_edits.html', {
            'last_edits': list(self.last_edits),
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

    root_page = get_explorable_root_page(request.user)
    if root_page:
        root_site = root_page.get_site()
    else:
        root_site = None

    real_site_name = None
    if root_site:
        real_site_name = root_site.site_name if root_site.site_name else root_site.hostname

    return render(request, "wagtailadmin/home.html", {
        'root_page': root_page,
        'root_site': root_site,
        'site_name': real_site_name if real_site_name else settings.WAGTAIL_SITE_NAME,
        'panels': sorted(panels, key=lambda p: p.order),
        'user': request.user
    })


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")
