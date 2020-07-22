from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.core import hooks
from wagtail.core.permissions import site_permission_policy

from .views import LocaleViewSet


@hooks.register('register_admin_viewset')
def register_viewset():
    return LocaleViewSet('wagtaillocales', url_prefix='locales')


class LocalesMenuItem(MenuItem):
    def is_shown(self, request):
        return site_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_locales_menu_item():
    return LocalesMenuItem(_('Locales'), reverse('wagtaillocales:index'),
                           icon_name='site', order=603)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailcore',
                                     codename__in=['add_locale', 'change_locale', 'delete_locale'])
