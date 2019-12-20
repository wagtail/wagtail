from django.conf.urls import include, url
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.contrib.search_promotions import admin_urls
from wagtail.core import hooks


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^searchpicks/', include(admin_urls, namespace='wagtailsearchpromotions')),
    ]


class SearchPicksMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('wagtailsearchpromotions.add_searchpromotion')
            or request.user.has_perm('wagtailsearchpromotions.change_searchpromotion')
            or request.user.has_perm('wagtailsearchpromotions.delete_searchpromotion')
        )


@hooks.register('register_settings_menu_item')
def register_search_picks_menu_item():
    return SearchPicksMenuItem(
        _('Promoted search results'),
        reverse('wagtailsearchpromotions:index'),
        classnames='icon icon-pick', order=900
    )


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtailsearchpromotions',
        codename__in=['add_searchpromotion', 'change_searchpromotion', 'delete_searchpromotion']
    )
