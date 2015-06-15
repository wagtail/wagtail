from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailredirects import urls

from wagtail.wagtailadmin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^redirects/', include(urls)),
    ]


class RedirectsMenuItem(MenuItem):
    def is_shown(self, request):
        # TEMPORARY: Only show if the user is a superuser
        return request.user.is_superuser

@hooks.register('register_settings_menu_item')
def register_redirects_menu_item():
    return RedirectsMenuItem(_('Redirects'), urlresolvers.reverse('wagtailredirects_index'), classnames='icon icon-redirect', order=800)
