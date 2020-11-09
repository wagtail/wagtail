from urllib.parse import urlencode

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.urls import include, path, reverse
from django.utils.translation import gettext as _
from django.views.i18n import JavaScriptCatalog

from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.admin.action_menu import ActionMenuItem as PageActionMenuItem
from wagtail.core import hooks
from wagtail.core.models import Locale, TranslatableMixin

from .views import SubmitPageTranslationView, SubmitSnippetTranslationView


# from simple_translation.models import TranslationSource


# The `wagtail.snippets.action_menu` module is introduced in https://github.com/wagtail/wagtail/pull/6384
# FIXME: Remove this check when this module is merged into master
try:
    from wagtail.snippets.action_menu import ActionMenuItem as SnippetActionMenuItem

    SNIPPET_RESTART_TRANSLATION_ENABLED = True
except ImportError:
    SNIPPET_RESTART_TRANSLATION_ENABLED = False

from wagtail.snippets.widgets import SnippetListingButton


@hooks.register("register_admin_urls")
def register_admin_urls():
    urls = [
        path(
            "submit/page/<int:page_id>/",
            SubmitPageTranslationView.as_view(),
            name="submit_page_translation",
        ),
        path(
            "submit/snippet/<slug:app_label>/<slug:model_name>/<str:pk>/",
            SubmitSnippetTranslationView.as_view(),
            name="submit_snippet_translation",
        ),
    ]

    return [
        path(
            "localize/",
            include(
                (urls, "simple_translation"),
                namespace="simple_translation",
            ),
        )
    ]


@hooks.register("register_page_listing_more_buttons")
def page_listing_more_buttons(page, page_perms, is_parent=False, next_url=None):
    # TODO add perm
    # if page_perms.user.has_perm('wagtail_localize.submit_translation') and not page.is_root():

    # If there's at least one locale that we haven't translated into yet, show "Translate this page" button
    has_locale_to_translate_to = Locale.objects.exclude(
        id__in=page.get_translations(inclusive=True).values_list("locale_id", flat=True)
    ).exists()

    if has_locale_to_translate_to:
        url = reverse("simple_translation:submit_page_translation", args=[page.id])
        if next_url is not None:
            url += "?" + urlencode({"next": next_url})

        yield wagtailadmin_widgets.Button(_("Translate"), url, priority=60)


@hooks.register("register_snippet_listing_buttons")
def register_snippet_listing_buttons(snippet, user, next_url=None):
    model = type(snippet)

    if issubclass(model, TranslatableMixin) and user.has_perm(
        "simple_translation.submit_translation"
    ):
        # If there's at least one locale that we haven't translated into yet, show "Translate" button
        has_locale_to_translate_to = Locale.objects.exclude(
            id__in=snippet.get_translations(inclusive=True).values_list(
                "locale_id", flat=True
            )
        ).exists()

        if has_locale_to_translate_to:
            url = reverse(
                "simple_translation:submit_snippet_translation",
                args=[model._meta.app_label, model._meta.model_name, quote(snippet.pk)],
            )
            if next_url is not None:
                url += "?" + urlencode({"next": next_url})

            yield SnippetListingButton(
                _("Translate"),
                url,
                attrs={
                    "aria-label": _("Translate '%(title)s'") % {"title": str(snippet)}
                },
                priority=100,
            )
