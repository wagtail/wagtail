from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtaileditorspicks import urls

from wagtail.wagtailadmin.menu import MenuItem


def register_admin_urls():
    return [
        url(r'^editorspicks/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def construct_main_menu(request, menu_items):
    # TEMPORARY: Only show if the user is a superuser
    if request.user.is_superuser:
        menu_items.append(
            MenuItem(_('Editors picks'), urlresolvers.reverse('wagtaileditorspicks_index'), classnames='icon icon-pick', order=900)
        )
hooks.register('construct_main_menu', construct_main_menu)
