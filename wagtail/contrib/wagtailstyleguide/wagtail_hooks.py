from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailimages import urls

from . import views


def register_admin_urls():
    return [
        url(r'^styleguide/$', views.index, name='wagtailstyleguide'),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def construct_main_menu(request, menu_items):
    menu_items.append(
        MenuItem(_('Styleguide'), urlresolvers.reverse('wagtailstyleguide'), classnames='icon icon-image', order=1000)
    )
hooks.register('construct_main_menu', construct_main_menu)
