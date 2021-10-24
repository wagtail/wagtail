from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.urls import include, path, reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from wagtail.admin.admin_url_finder import ModelAdminURLFinder, register_admin_url_finder
from wagtail.admin.menu import MenuItem
from wagtail.admin.search import SearchArea
from wagtail.core import hooks
from wagtail.core.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.core.permission_policies import ModelPermissionPolicy
from wagtail.users.urls import users
from wagtail.users.utils import user_can_delete_user
from wagtail.users.views.bulk_actions import (
    AssignRoleBulkAction, DeleteBulkAction, SetActiveStateBulkAction)
from wagtail.users.widgets import UserListingButton


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('users/', include(users, namespace='wagtailusers_users')),
    ]


def get_group_viewset_cls(app_config):
    try:
        group_viewset_cls = import_string(app_config.group_viewset)
    except (AttributeError, ImportError) as e:
        raise ImproperlyConfigured(
            "Invalid setting for {appconfig}.group_viewset: {message}".format(
                appconfig=app_config.__class__.__name__,
                message=e
            )
        )
    return group_viewset_cls


@hooks.register('register_admin_viewset')
def register_viewset():
    app_config = apps.get_app_config("wagtailusers")
    group_viewset_cls = get_group_viewset_cls(app_config)
    return group_viewset_cls('wagtailusers_groups', url_prefix='groups')


# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
delete_user_perm = "{0}.delete_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


class UsersMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register('register_settings_menu_item')
def register_users_menu_item():
    return UsersMenuItem(
        _('Users'),
        reverse('wagtailusers_users:index'),
        icon_name='user',
        order=600
    )


class GroupsMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('auth.add_group')
            or request.user.has_perm('auth.change_group')
            or request.user.has_perm('auth.delete_group')
        )


@hooks.register('register_settings_menu_item')
def register_groups_menu_item():
    return GroupsMenuItem(
        _('Groups'),
        reverse('wagtailusers_groups:index'),
        icon_name='group',
        order=601
    )


@hooks.register('register_permissions')
def register_permissions():
    user_permissions = Q(content_type__app_label=AUTH_USER_APP_LABEL, codename__in=[
        'add_%s' % AUTH_USER_MODEL_NAME.lower(),
        'change_%s' % AUTH_USER_MODEL_NAME.lower(),
        'delete_%s' % AUTH_USER_MODEL_NAME.lower(),
    ])
    group_permissions = Q(content_type__app_label='auth', codename__in=['add_group', 'change_group', 'delete_group'])

    return Permission.objects.filter(user_permissions | group_permissions)


class UsersSearchArea(SearchArea):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register('register_admin_search_area')
def register_users_search_area():
    return UsersSearchArea(
        _('Users'), reverse('wagtailusers_users:index'),
        name='users',
        icon_name='user',
        order=600)


@hooks.register('register_user_listing_buttons')
def user_listing_buttons(context, user):
    yield UserListingButton(_('Edit'), reverse('wagtailusers_users:edit', args=[user.pk]), attrs={'title': _('Edit this user')}, priority=10)
    if user_can_delete_user(context.request.user, user):
        yield UserListingButton(_('Delete'), reverse('wagtailusers_users:delete', args=[user.pk]), classes={'no'}, attrs={'title': _('Delete this user')}, priority=20)


User = get_user_model()


class UserAdminURLFinder(ModelAdminURLFinder):
    edit_url_name = 'wagtailusers_users:edit'
    permission_policy = ModelPermissionPolicy(User)


register_admin_url_finder(User, UserAdminURLFinder)


for action_class in [AssignRoleBulkAction, DeleteBulkAction, SetActiveStateBulkAction]:
    hooks.register('register_bulk_action', action_class)
