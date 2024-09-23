from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.permissions import site_permission_policy

from .views import SiteViewSet


@hooks.register("register_admin_viewset")
def register_viewset():
    return SiteViewSet("wagtailsites", url_prefix="sites")


class SitesMenuItem(MenuItem):
    def is_shown(self, request):
        return site_permission_policy.user_has_any_permission(
            request.user, ["add", "change", "delete"]
        )


@hooks.register("register_settings_menu_item")
def register_sites_menu_item():
    return SitesMenuItem(
        _("Sites"),
        reverse("wagtailsites:index"),
        name="sites",
        icon_name="site",
        order=602,
    )
