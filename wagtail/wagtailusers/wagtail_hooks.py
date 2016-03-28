from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.models import Permission
from django.core import urlresolvers
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailadmin.search import SearchArea
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.wagtailusers.urls import groups, users


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^users/', include(users, app_name='wagtailusers_users', namespace='wagtailusers_users')),
        url(r'^groups/', include(groups, app_name='wagtailusers_groups', namespace='wagtailusers_groups')),
    ]


# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
delete_user_perm = "{0}.delete_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


class UsersMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm) or
            request.user.has_perm(change_user_perm) or
            request.user.has_perm(delete_user_perm)
        )


@hooks.register('register_settings_menu_item')
def register_users_menu_item():
    return UsersMenuItem(
        _('Users'),
        urlresolvers.reverse('wagtailusers_users:index'),
        classnames='icon icon-user',
        order=600
    )


class GroupsMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('auth.add_group') or
            request.user.has_perm('auth.change_group') or
            request.user.has_perm('auth.delete_group')
        )


@hooks.register('register_settings_menu_item')
def register_groups_menu_item():
    return GroupsMenuItem(
        _('Groups'),
        urlresolvers.reverse('wagtailusers_groups:index'),
        classnames='icon icon-group',
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
            request.user.has_perm(add_user_perm) or
            request.user.has_perm(change_user_perm) or
            request.user.has_perm(delete_user_perm)
        )


@hooks.register('register_admin_search_area')
def register_users_search_area():
    return UsersSearchArea(
        _('Users'), urlresolvers.reverse('wagtailusers_users:index'),
        name='users',
        classnames='icon icon-user',
        order=600)
