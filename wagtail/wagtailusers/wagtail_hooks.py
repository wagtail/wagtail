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
        url(r'^users/', include(users)),
        url(r'^groups/', include(groups)),
    ]


class AuthMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_module_perms('auth')

@hooks.register('register_settings_menu_item')
def register_users_menu_item():
    return AuthMenuItem(_('Users'), urlresolvers.reverse('wagtailusers_users_index'), classnames='icon icon-user', order=600)

@hooks.register('register_settings_menu_item')
def register_groups_menu_item():
    return AuthMenuItem(_('Groups'), urlresolvers.reverse('wagtailusers_groups_index'), classnames='icon icon-group', order=601)


@hooks.register('register_permissions')
def register_permissions():
    user_profile_content_types = ContentType.objects.filter(app_label='wagtailusers', model='userprofile')
    auth_content_types = ContentType.objects.filter(app_label='auth', model__in=['group', 'user'])
    relevant_content_types = user_profile_content_types | auth_content_types
    return Permission.objects.filter(content_type__in=relevant_content_types)
