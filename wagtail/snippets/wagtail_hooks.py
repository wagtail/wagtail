from django.urls import include, path, reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.bulk_actions.delete import DeleteBulkAction
from wagtail.snippets.permissions import user_can_access_snippets
from wagtail.snippets.views import snippets as snippet_views


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
    def _snippets_in_index_view(self):
        return snippet_views.get_snippet_models_for_index_view()

    def is_shown(self, request):
        return user_can_access_snippets(request.user, self._snippets_in_index_view)


@hooks.register("register_admin_menu_item")
def register_snippets_menu_item():
    return SnippetsMenuItem(
        _("Snippets"),
        reverse("wagtailsnippets:index"),
        name="snippets",
        icon_name="snippet",
        order=500,
    )


hooks.register("register_bulk_action", DeleteBulkAction)
