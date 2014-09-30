from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailsites import urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^sites/', include(urls)),
    ]


class SitesMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.is_superuser

@hooks.register('register_settings_menu_item')
def register_sites_menu_item():
    return MenuItem(_('Sites'), urlresolvers.reverse('wagtailsites_index'), classnames='icon icon-site', order=602)
