from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailsites import urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^sites/', include(urls, app_name='wagtailsites', namespace='wagtailsites')),
    ]


class SitesMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('wagtailcore.add_site')
            or request.user.has_perm('wagtailcore.change_site')
            or request.user.has_perm('wagtailcore.delete_site')
        )


@hooks.register('register_settings_menu_item')
def register_sites_menu_item():
    return SitesMenuItem(_('Sites'), urlresolvers.reverse('wagtailsites:index'),
                         classnames='icon icon-site', order=602)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailcore',
                                     codename__in=['add_site', 'change_site', 'delete_site'])
