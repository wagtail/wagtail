from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem

from . import views


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("styleguide/", views.IndexView.as_view(), name="wagtailstyleguide"),
    ]


@hooks.register("register_settings_menu_item")
def register_styleguide_menu_item():
    return MenuItem(
        _("Styleguide"),
        reverse("wagtailstyleguide"),
        name="styleguide",
        icon_name="image",
        order=1000,
    )
