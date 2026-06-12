from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin

from wagtail import hooks
from wagtail.actions.move_page import MovePageAction
from wagtail.admin import messages
from wagtail.admin.forms.pages import MoveForm
from wagtail.models import Page


class MoveChooseDestinationView(TemplateView, FormMixin):
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


class MoveConfirmView(TemplateView):
    template_name = "wagtailadmin/pages/confirm_move.html"

    def dispatch(self, request, page_to_move_id, destination_id, *args, **kwargs):
        self.page_to_move = get_object_or_404(Page, id=page_to_move_id).specific
        # Needs .specific_deferred because the .get_admin_display_title method is called in template
        self.destination = get_object_or_404(Page, id=destination_id).specific_deferred
        self.i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)

        if not Page._slug_is_available(
            self.page_to_move.slug, self.destination, page=self.page_to_move
        ):
            messages.error(
                request,
                _(
                    "The slug '%(page_slug)s' is already in use at the selected parent page. Make sure the slug is unique and try again."
                )
                % {"page_slug": self.page_to_move.slug},
            )
            return redirect(
                "wagtailadmin_pages:move",
                self.page_to_move.id,
            )

        for fn in hooks.get_hooks("before_move_page"):
            result = fn(request, self.page_to_move, self.destination)
            if hasattr(result, "status_code"):
                return result

        self.pages_to_move = {self.page_to_move}

        # The `construct_translated_pages_to_cascade_actions` hook returns translation and
        # alias pages when the action is set to "move"
        if self.i18n_enabled:
            for fn in hooks.get_hooks("construct_translated_pages_to_cascade_actions"):
                fn_pages = fn([self.page_to_move], "move")
                if fn_pages and isinstance(fn_pages, dict):
                    for additional_pages in fn_pages.values():
                        self.pages_to_move.update(additional_pages)

        self.pages_to_move = list(self.pages_to_move)
        return super().dispatch(
            request, page_to_move_id, destination_id, *args, **kwargs
        )

    def post(self, request, *args, **kwargs):
        if self.i18n_enabled:
            # Get the list of translations of the page's original parent, which we
            # will use to determine whether translations will also be moved
            parent_page_translations = self.page_to_move.get_parent().get_translations()

        # any invalid moves *should* be caught by the permission check in the action
        # class, so don't bother to catch InvalidMoveToDescendant
        action = MovePageAction(
            self.page_to_move, self.destination, pos="last-child", user=request.user
        )
        action.execute()

        if self.i18n_enabled:
            # Move translation and alias pages if they have the same parent page.
            for translation in self.pages_to_move:
                if translation.get_parent() in parent_page_translations:
                    # Move the translated or alias page to its translated or
                    # alias "destination" page. The destination may not have
                    # been translated to the translation's locale, e.g. if it
                    # was created while the tree was not synced, so check for
                    # that before trying to move the page.
                    destination_translation = self.destination.get_translation_or_none(
                        translation.locale
                    )
                    if destination_translation:
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
            % {"page_title": self.page_to_move.get_admin_display_title()},
            buttons=[
                messages.button(
                    reverse("wagtailadmin_pages:edit", args=(self.page_to_move.id,)),
                    _("Edit"),
                )
            ],
        )

        for fn in hooks.get_hooks("after_move_page"):
            result = fn(request, self.page_to_move)
            if hasattr(result, "status_code"):
                return result

        return redirect("wagtailadmin_explore", self.destination.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_to_move": self.page_to_move,
                "destination": self.destination,
                "translations_to_move_count": len(
                    [
                        translation.id
                        for translation in self.pages_to_move
                        if not translation.alias_of_id
                        and translation.id != self.page_to_move.id
                    ]
                ),
            },
        )
        return context
