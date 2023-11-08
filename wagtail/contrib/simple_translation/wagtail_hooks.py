from typing import List

from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.urls import include, path, reverse
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.models import Locale, Page, TranslatableMixin
from wagtail.snippets.widgets import SnippetListingButton

from .views import SubmitPageTranslationView, SubmitSnippetTranslationView


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
            "translation/",
            include(
                (urls, "simple_translation"),
                namespace="simple_translation",
            ),
        )
    ]


@hooks.register("register_permissions")
def register_submit_translation_permission():
    return Permission.objects.filter(
        content_type__app_label="simple_translation", codename="submit_translation"
    )


@hooks.register("register_page_listing_more_buttons")
def page_listing_more_buttons(page, user, next_url=None):
    if user.has_perm("simple_translation.submit_translation") and not page.is_root():
        # If there's at least one locale that we haven't translated into yet,
        # show "Translate this page" button
        has_locale_to_translate_to = Locale.objects.exclude(
            id__in=page.get_translations(inclusive=True).values_list(
                "locale_id", flat=True
            )
        ).exists()

        if has_locale_to_translate_to:
            url = reverse("simple_translation:submit_page_translation", args=[page.id])
            yield wagtailadmin_widgets.Button(_("Translate"), url, priority=60)


@hooks.register("register_page_header_buttons")
def page_header_buttons(page, user, view_name, next_url=None):
    if not page.is_root() and user.has_perm("simple_translation.submit_translation"):
        # If there's at least one locale that we haven't translated into yet,
        # show "Translate this page" button
        has_locale_to_translate_to = Locale.objects.exclude(
            id__in=page.get_translations(inclusive=True).values_list(
                "locale_id", flat=True
            )
        ).exists()

        if has_locale_to_translate_to:
            url = reverse("simple_translation:submit_page_translation", args=[page.id])
            yield wagtailadmin_widgets.Button(
                _("Translate"),
                url,
                icon_name="globe",
                attrs={
                    "title": _("Translate this page")
                    % {"title": page.get_admin_display_title()}
                },
                priority=80,
            )


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
            yield SnippetListingButton(
                _("Translate"),
                url,
                attrs={
                    "aria-label": _("Translate '%(title)s'") % {"title": str(snippet)}
                },
                priority=100,
            )


@hooks.register("construct_translated_pages_to_cascade_actions")
def construct_translated_pages_to_cascade_actions(pages: List[Page], action: str):
    if not getattr(settings, "WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE", False):
        return

    page_list = {}
    if action == "unpublish":
        # Only return non-alias translations of the page
        for page in pages:
            page_list[page] = Page.objects.translation_of(page, inclusive=False).filter(
                alias_of__isnull=True
            )
    elif action == "move" or action == "delete":
        # Return all translations or aliases in other trees
        for page in pages:
            page_list[page] = Page.objects.translation_of(page, inclusive=False)

    return page_list
