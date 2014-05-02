from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtaildocs import admin_urls


def register_admin_urls():
    return [
        url(r'^documents/', include(admin_urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def construct_main_menu(request, menu_items):
    if request.user.has_perm('wagtaildocs.add_document'):
        menu_items.append(
            MenuItem(_('Documents'), urlresolvers.reverse('wagtaildocs_index'), classnames='icon icon-doc-full-inverse', order=400)
        )
hooks.register('construct_main_menu', construct_main_menu)
