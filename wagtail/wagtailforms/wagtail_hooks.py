from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailforms import urls
from wagtail.wagtailforms.models import get_form_types


def register_admin_urls():
    return [
        url(r'^forms/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)

def construct_main_menu(request, menu_items):
    if get_form_types():  # show this only if forms actually exist.
        # TODO: Limit this to only show the menu item if the user has permission to access at least one form page
        menu_items.append(
            MenuItem(_('Forms'), urlresolvers.reverse('wagtailforms_index'), classnames='icon icon-grip', order=700)
        )
hooks.register('construct_main_menu', construct_main_menu)
