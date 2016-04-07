from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks

from . import views


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^styleguide/$', views.index, name='wagtailstyleguide'),
    ]


@hooks.register('register_settings_menu_item')
def register_styleguide_menu_item():
    return MenuItem(
        _('Styleguide'),
        urlresolvers.reverse('wagtailstyleguide'),
        classnames='icon icon-image',
        order=1000
    )
