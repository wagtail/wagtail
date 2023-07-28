from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import include, path, reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.bulk_actions.delete import DeleteBulkAction
from wagtail.snippets.models import get_snippet_models
from wagtail.snippets.permissions import (
    user_can_edit_snippet_type,
    user_can_edit_snippets,
)
from wagtail.snippets.views import snippets as snippet_views
from wagtail.snippets.widgets import SnippetListingButton


@hooks.register("register_admin_urls")
def register_admin_urls():
    snippet_index_patterns = (
        [
            path("", snippet_views.ModelIndexView.as_view(), name="index"),
        ],
        "wagtailsnippets",
    )

    return [
        path("snippets/", include(snippet_index_patterns)),
    ]


class SnippetsMenuItem(MenuItem):
    @cached_property
    def _all_have_menu_items(self):
        return all(
            model.snippet_viewset.get_menu_item_is_registered()
            for model in get_snippet_models()
        )

    def is_shown(self, request):
        return not self._all_have_menu_items and user_can_edit_snippets(request.user)


@hooks.register("register_admin_menu_item")
def register_snippets_menu_item():
    return SnippetsMenuItem(
        _("Snippets"),
        reverse("wagtailsnippets:index"),
        name="snippets",
        icon_name="snippet",
        order=500,
    )


@hooks.register("register_permissions")
def register_permissions():
    content_types = ContentType.objects.get_for_models(*get_snippet_models()).values()
    return Permission.objects.filter(content_type__in=content_types)


@hooks.register("register_snippet_listing_buttons")
def register_snippet_listing_buttons(snippet, user, next_url=None):
    model = type(snippet)
    viewset = model.snippet_viewset
    permission_policy = viewset.permission_policy

    if user_can_edit_snippet_type(user, model):
        yield SnippetListingButton(
            _("Edit"),
            reverse(
                viewset.get_url_name("edit"),
                args=[quote(snippet.pk)],
            ),
            attrs={"aria-label": _("Edit '%(title)s'") % {"title": str(snippet)}},
            priority=10,
        )

    if viewset.inspect_view_enabled and permission_policy.user_has_any_permission(
        user, viewset.inspect_view_class.any_permission_required
    ):

        yield SnippetListingButton(
            _("Inspect"),
            reverse(
                viewset.get_url_name("inspect"),
                args=[quote(snippet.pk)],
            ),
            attrs={"aria-label": _("Inspect '%(title)s'") % {"title": str(snippet)}},
            priority=20,
        )

    if permission_policy.user_has_permission(user, "delete"):
        yield SnippetListingButton(
            _("Delete"),
            reverse(
                viewset.get_url_name("delete"),
                args=[quote(snippet.pk)],
            ),
            attrs={"aria-label": _("Delete '%(title)s'") % {"title": str(snippet)}},
            priority=30,
            classes=["no"],
        )


hooks.register("register_bulk_action", DeleteBulkAction)
