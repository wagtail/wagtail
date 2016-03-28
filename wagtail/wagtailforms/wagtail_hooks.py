from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks
from wagtail.wagtailforms import urls
from wagtail.wagtailforms.models import get_forms_for_user


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^forms/', include(urls, app_name='wagtailforms', namespace='wagtailforms')),
    ]


class FormsMenuItem(MenuItem):
    def is_shown(self, request):
        # show this only if the user has permission to retrieve submissions for at least one form
        return get_forms_for_user(request.user).exists()


@hooks.register('register_admin_menu_item')
def register_forms_menu_item():
    return FormsMenuItem(
        _('Forms'), urlresolvers.reverse('wagtailforms:index'),
        name='forms', classnames='icon icon-form', order=700
    )
