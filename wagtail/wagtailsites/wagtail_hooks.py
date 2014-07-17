from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailsites import urls


def register_admin_urls():
    return [
        url(r'^sites/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def construct_main_menu(request, menu_items):
    if request.user.is_superuser:
        menu_items.append(
            MenuItem(_('Sites'), urlresolvers.reverse('wagtailsites_index'), classnames='icon icon-site', order=602)
        )
hooks.register('construct_main_menu', construct_main_menu)
