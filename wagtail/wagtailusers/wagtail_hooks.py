from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailusers import urls


def register_admin_urls():
    return [
        url(r'^users/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def construct_main_menu(request, menu_items):
    if request.user.has_module_perms('auth'):
        menu_items.append(
            MenuItem(_('Users'), urlresolvers.reverse('wagtailusers_index'), classnames='icon icon-user', order=600)
        )
hooks.register('construct_main_menu', construct_main_menu)
