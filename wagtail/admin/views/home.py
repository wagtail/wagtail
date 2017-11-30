from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db import connection
from django.db.models import Max
from django.http import Http404
from django.shortcuts import render
from django.template.loader import render_to_string

from wagtail.admin.navigation import get_explorable_root_page
from wagtail.admin.site_summary import SiteSummaryPanel
from wagtail.core import hooks
from wagtail.core.models import Page, PageRevision, UserPagePermissionsProxy

User = get_user_model()


# Panels for the homepage

class UpgradeNotificationPanel:
    name = 'upgrade_notification'
    order = 100

    def __init__(self, request):
        self.request = request

    def render(self):
        if self.request.user.is_superuser and getattr(settings, "WAGTAIL_ENABLE_UPDATE_CHECK", True):
            return render_to_string('wagtailadmin/home/upgrade_notification.html', {}, request=self.request)
        else:
            return ""


class PagesForModerationPanel:
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


class RecentEditsPanel:
    name = 'recent_edits'
    order = 300

    def __init__(self, request):
        self.request = request

        # Last n edited pages
        edit_count = getattr(settings, 'WAGTAILADMIN_RECENT_EDITS_LIMIT', 5)
        if connection.vendor == 'mysql':
            # MySQL can't handle the subselect created by the ORM version -
            # it fails with "This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'"
            last_edits = PageRevision.objects.raw(
                """
                SELECT wp.* FROM
                    wagtailcore_pagerevision wp JOIN (
                        SELECT max(created_at) AS max_created_at, page_id FROM
                            wagtailcore_pagerevision WHERE user_id = %s GROUP BY page_id ORDER BY max_created_at DESC LIMIT %s
                    ) AS max_rev ON max_rev.max_created_at = wp.created_at ORDER BY wp.created_at DESC
                 """, [
                    User._meta.pk.get_db_prep_value(self.request.user.pk, connection),
                    edit_count
                ]
            )
        else:
            last_edits_dates = (PageRevision.objects.filter(user=self.request.user)
                                .values('page_id').annotate(latest_date=Max('created_at'))
                                .order_by('-latest_date').values('latest_date')[:edit_count])
            last_edits = PageRevision.objects.filter(created_at__in=last_edits_dates).order_by('-created_at')

        page_keys = [pr.page_id for pr in last_edits]
        pages = Page.objects.specific().in_bulk(page_keys)
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


@permission_required('wagtailadmin.access_admin', login_url='wagtailadmin_login')
def default(request):
    """
    Called whenever a request comes in with the correct prefix (eg /admin/) but
    doesn't actually correspond to a Wagtail view.

    For authenticated users, it'll raise a 404 error. Anonymous users will be
    redirected to the login page.
    """
    raise Http404
