from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.contrib.wagtailsearchpicks import admin_urls

from wagtail.wagtailadmin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^searchpicks/', include(admin_urls, namespace='wagtailsearchpromotions')),
    ]


class SearchPicksMenuItem(MenuItem):
    def is_shown(self, request):
        # TEMPORARY: Only show if the user is a superuser
        return request.user.is_superuser


@hooks.register('register_settings_menu_item')
def register_search_picks_menu_item():
    return SearchPicksMenuItem(_('Promoted search results'), urlresolvers.reverse('wagtailsearchpromotions:index'), classnames='icon icon-pick', order=900)
