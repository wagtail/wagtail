from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailsearch.urls import admin as admin_urls

from wagtail.wagtailadmin.menu import MenuItem


def register_admin_urls():
    return [
        url(r'^search/', include(admin_urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def construct_main_menu(request, menu_items):
    # TEMPORARY: Only show if the user is a superuser
    if request.user.is_superuser:
        menu_items.append(
            MenuItem(_('Editors picks'), urlresolvers.reverse('wagtailsearch_editorspicks_index'), classnames='icon icon-pick', order=900)
        )
hooks.register('construct_main_menu', construct_main_menu)
