from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission

from wagtail.wagtailcore import hooks
from wagtail.wagtailredirects import urls

from wagtail.wagtailadmin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^redirects/', include(urls, app_name='wagtailredirects', namespace='wagtailredirects')),
    ]


class RedirectsMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm('wagtailredirects.add_redirect')
            or request.user.has_perm('wagtailredirects.change_redirect')
            or request.user.has_perm('wagtailredirects.delete_redirect')
        )


@hooks.register('register_settings_menu_item')
def register_redirects_menu_item():
    return RedirectsMenuItem(
        _('Redirects'), urlresolvers.reverse('wagtailredirects:index'), classnames='icon icon-redirect', order=800
    )


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailredirects',
                                     codename__in=['add_redirect', 'change_redirect', 'delete_redirect'])
