from django.contrib.auth.models import Permission
from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.menu import MenuItem
from wagtail.contrib.redirects import urls
from wagtail.contrib.redirects.permissions import permission_policy

from .models import Redirect


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("redirects/", include(urls, namespace="wagtailredirects")),
    ]


class RedirectsMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ["add", "change", "delete"]
        )


@hooks.register("register_settings_menu_item")
def register_redirects_menu_item():
    return RedirectsMenuItem(
        _("Redirects"),
        reverse("wagtailredirects:index"),
        icon_name="redirect",
        order=800,
    )


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label="wagtailredirects",
        codename__in=["add_redirect", "change_redirect", "delete_redirect"],
    )


class RedirectAdminURLFinder(ModelAdminURLFinder):
    edit_url_name = "wagtailredirects:edit"
    permission_policy = permission_policy


register_admin_url_finder(Redirect, RedirectAdminURLFinder)
