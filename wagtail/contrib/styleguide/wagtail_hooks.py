from django.conf.urls import url
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.core import hooks

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
        reverse('wagtailstyleguide'),
        classnames='icon icon-image',
        order=1000
    )
