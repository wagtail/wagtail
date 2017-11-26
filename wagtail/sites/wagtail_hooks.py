from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.core import hooks
from wagtail.core.permissions import site_permission_policy

from .views import SiteViewSet


@hooks.register('register_admin_viewset')
def register_viewset():
    return SiteViewSet('wagtailsites', url_prefix='sites')


class SitesMenuItem(MenuItem):
    def is_shown(self, request):
        return site_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_sites_menu_item():
    return SitesMenuItem(_('Sites'), reverse('wagtailsites:index'),
                         classnames='icon icon-site', order=602)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailcore',
                                     codename__in=['add_site', 'change_site', 'delete_site'])
