from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.models import Permission
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.permissions import site_permission_policy
from wagtail.wagtailsites import urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^sites/', include(urls, app_name='wagtailsites', namespace='wagtailsites')),
    ]


class SitesMenuItem(MenuItem):
    def is_shown(self, request):
        return site_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_sites_menu_item():
    return SitesMenuItem(_('Sites'), urlresolvers.reverse('wagtailsites:index'),
                         classnames='icon icon-site', order=602)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailcore',
                                     codename__in=['add_site', 'change_site', 'delete_site'])
