from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailusers import urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^users/', include(urls)),
    ]


class UsersMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_module_perms('auth')

@hooks.register('register_admin_menu_item')
def register_users_menu_item():
    return UsersMenuItem(_('Users'), urlresolvers.reverse('wagtailusers_index'), classnames='icon icon-user', order=600)
