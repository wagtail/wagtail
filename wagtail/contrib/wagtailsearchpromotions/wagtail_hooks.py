from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission

from wagtail.wagtailcore import hooks
from wagtail.contrib.wagtailsearchpromotions import admin_urls

from wagtail.wagtailadmin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^searchpicks/', include(admin_urls, app_name='wagtailsearchpromotions', namespace='wagtailsearchpromotions')),
    ]


class SearchPicksMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('wagtailsearchpromotions.add_searchpromotion') or
            request.user.has_perm('wagtailsearchpromotions.change_searchpromotion') or
            request.user.has_perm('wagtailsearchpromotions.delete_searchpromotion')
        )


@hooks.register('register_settings_menu_item')
def register_search_picks_menu_item():
    return SearchPicksMenuItem(
        _('Promoted search results'),
        urlresolvers.reverse('wagtailsearchpromotions:index'),
        classnames='icon icon-pick', order=900
    )


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtailsearchpromotions',
        codename__in=['add_searchpromotion', 'change_searchpromotion', 'delete_searchpromotion']
    )
