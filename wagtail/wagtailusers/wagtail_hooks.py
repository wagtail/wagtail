from django.conf.urls import include, url
from django.core import urlresolvers
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailusers.urls import users, groups


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^users/', include(users, namespace='wagtailusers_users')),
        url(r'^groups/', include(groups, namespace='wagtailusers_groups')),
    ]


class UsersMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_module_perms('auth')


@hooks.register('register_settings_menu_item')
def register_users_menu_item():
    return UsersMenuItem(_('Users'), urlresolvers.reverse('wagtailusers_users:index'), classnames='icon icon-user', order=600)


class GroupsMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('auth.add_group')
            or request.user.has_perm('auth.change_group')
            or request.user.has_perm('auth.delete_group')
        )


@hooks.register('register_settings_menu_item')
def register_groups_menu_item():
    return GroupsMenuItem(_('Groups'), urlresolvers.reverse('wagtailusers_groups:index'), classnames='icon icon-group', order=601)


@hooks.register('register_permissions')
def register_permissions():
    auth_content_types = ContentType.objects.filter(app_label='auth', model__in=['group', 'user'])
    relevant_content_types = auth_content_types
    return Permission.objects.filter(content_type__in=relevant_content_types)
