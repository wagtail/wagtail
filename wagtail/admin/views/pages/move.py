from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin

from wagtail import hooks
from wagtail.actions.move_page import MovePageAction
from wagtail.admin import messages
from wagtail.admin.forms.pages import MoveForm
from wagtail.models import Page


def get_translated_pages_to_move(page_to_move, destination):
    translated_pages_to_move = []

    if not getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        return translated_pages_to_move

    additional_pages = set()

    # The `construct_translated_pages_to_cascade_actions` hook returns translation
    # and alias pages when the action is set to "move".
    for fn in hooks.get_hooks("construct_translated_pages_to_cascade_actions"):
        fn_pages = fn([page_to_move], "move")
        if fn_pages and isinstance(fn_pages, dict):
            for pages in fn_pages.values():
                additional_pages.update(pages)

    if not additional_pages:
        return translated_pages_to_move

    parent_page_translations = {
        translation.locale_id: translation
        for translation in page_to_move.get_parent().get_translations()
    }
    destination_translations = {
        translation.locale_id: translation
        for translation in destination.get_translations()
    }

    for translation in additional_pages:
        translated_parent = parent_page_translations.get(translation.locale_id)
        destination_translation = destination_translations.get(translation.locale_id)

        if (
            translated_parent
            and destination_translation
            and translation.get_parent().id == translated_parent.id
        ):
            translated_pages_to_move.append((translation, destination_translation))

    return translated_pages_to_move


class MoveChooseDestination(TemplateView, FormMixin):
    template_name = "wagtailadmin/pages/move_choose_destination.html"
    form_class = MoveForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.page_to_move = get_object_or_404(Page, id=kwargs["page_to_move_id"])
        self.page_perms = self.page_to_move.permissions_for_user(request.user)

        if not self.page_perms.can_move():
            raise PermissionDenied

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        target_parent_models = set(
            self.page_to_move.specific_class.allowed_parent_page_models()
        )
        kwargs["target_parent_models"] = target_parent_models
        kwargs["page_to_move"] = self.page_to_move

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_to_move"] = self.page_to_move
        context["move_form"] = self.get_form()

        return context

    def form_valid(self, form):
        # Receive the new parent page (this should never be empty)
        if form.cleaned_data["new_parent_page"]:
            new_parent_page = form.cleaned_data["new_parent_page"]
            return redirect(
                "wagtailadmin_pages:move_confirm",
                self.page_to_move.id,
                new_parent_page.id,
            )
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


def move_confirm(request, page_to_move_id, destination_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id).specific
    # Needs .specific_deferred because the .get_admin_display_title method is called in template
    destination = get_object_or_404(Page, id=destination_id).specific_deferred

    if not Page._slug_is_available(page_to_move.slug, destination, page=page_to_move):
        messages.error(
            request,
            _(
                "The slug '%(page_slug)s' is already in use at the selected parent page. Make sure the slug is unique and try again."
            )
            % {"page_slug": page_to_move.slug},
        )
        return redirect(
            "wagtailadmin_pages:move",
            page_to_move.id,
        )

    for fn in hooks.get_hooks("before_move_page"):
        result = fn(request, page_to_move, destination)
        if hasattr(result, "status_code"):
            return result

    translated_pages_to_move = get_translated_pages_to_move(page_to_move, destination)

    if request.method == "POST":
        # any invalid moves *should* be caught by the permission check in the action
        # class, so don't bother to catch InvalidMoveToDescendant
        action = MovePageAction(
            page_to_move, destination, pos="last-child", user=request.user
        )
        action.execute()

        for translation, destination_translation in translated_pages_to_move:
            action = MovePageAction(
                translation,
                destination_translation,
                pos="last-child",
                user=request.user,
            )
            action.execute()

        messages.success(
            request,
            _("Page '%(page_title)s' moved.")
            % {"page_title": page_to_move.get_admin_display_title()},
            buttons=[
                messages.button(
                    reverse("wagtailadmin_pages:edit", args=(page_to_move.id,)),
                    _("Edit"),
                )
            ],
        )

        for fn in hooks.get_hooks("after_move_page"):
            result = fn(request, page_to_move)
            if hasattr(result, "status_code"):
                return result

        return redirect("wagtailadmin_explore", destination.id)

    return TemplateResponse(
        request,
        "wagtailadmin/pages/confirm_move.html",
        {
            "page_to_move": page_to_move,
            "destination": destination,
            "translations_to_move_count": len(
                [
                    translation.id
                    for translation, _destination_translation in translated_pages_to_move
                    if not translation.alias_of_id
                ]
            ),
        },
    )
