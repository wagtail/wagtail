from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import include, path, reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets import urls
from wagtail.snippets.models import get_snippet_models
from wagtail.snippets.permissions import (
    get_permission_name,
    user_can_edit_snippet_type,
    user_can_edit_snippets,
)
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.snippets.widgets import SnippetListingButton


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("snippets/", include(urls, namespace="wagtailsnippets")),
    ]


@hooks.register("register_admin_viewset")
def register_viewsets():
    viewsets = []
    for model in get_snippet_models():
        admin_viewset = getattr(model, "admin_viewset", None) or SnippetViewSet
        if isinstance(admin_viewset, str):
            admin_viewset = import_string(admin_viewset)

        viewsets += [
            admin_viewset(
                model.get_admin_url_namespace(),
                model=model,
                url_prefix=model.get_admin_base_path(),
            )
        ]
    return viewsets


class SnippetsMenuItem(MenuItem):
    def is_shown(self, request):
        return user_can_edit_snippets(request.user)


@hooks.register("register_admin_menu_item")
def register_snippets_menu_item():
    return SnippetsMenuItem(
        _("Snippets"), reverse("wagtailsnippets:index"), icon_name="snippet", order=500
    )


@hooks.register("register_permissions")
def register_permissions():
    content_types = ContentType.objects.get_for_models(*get_snippet_models()).values()
    return Permission.objects.filter(content_type__in=content_types)


@hooks.register("register_snippet_listing_buttons")
def register_snippet_listing_buttons(snippet, user, next_url=None):
    model = type(snippet)

    if user_can_edit_snippet_type(user, model):
        yield SnippetListingButton(
            _("Edit"),
            reverse(
                f"wagtailsnippets_{model._meta.app_label}_{model._meta.model_name}:edit",
                args=[quote(snippet.pk)],
            ),
            attrs={"aria-label": _("Edit '%(title)s'") % {"title": str(snippet)}},
            priority=10,
        )

    if user.has_perm(get_permission_name("delete", model)):
        yield SnippetListingButton(
            _("Delete"),
            reverse(
                f"wagtailsnippets_{model._meta.app_label}_{model._meta.model_name}:delete",
                args=[quote(snippet.pk)],
            ),
            attrs={"aria-label": _("Delete '%(title)s'") % {"title": str(snippet)}},
            priority=20,
            classes=["no"],
        )
