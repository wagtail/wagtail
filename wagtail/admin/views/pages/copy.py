from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import FormView

from wagtail import hooks
from wagtail.actions.copy_page import CopyPageAction
from wagtail.actions.create_alias import CreatePageAliasAction
from wagtail.admin import messages
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.models import Page


class CopyView(FormView):
    template_name = "wagtailadmin/pages/copy.html"

    def dispatch(self, request, page_id, *args, **kwargs):
        self.page = get_object_or_404(Page, id=page_id)
        page_perms = self.page.permissions_for_user(request.user)
        if not page_perms.can_copy():
            raise PermissionDenied

        # Parent page defaults to parent of source page
        self.parent_page = self.page.get_parent()

        self.next_url = get_valid_next_url_from_request(request)

        for fn in hooks.get_hooks("before_copy_page"):
            result = fn(request, self.page)
            if hasattr(result, "status_code"):
                return result

        return super().dispatch(request, page_id, *args, **kwargs)

    def get_form_class(self):
        return getattr(self.page.specific_class, "copy_form_class", CopyForm)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["page"] = self.page
        return kwargs

    def post(self, request, page_id, *args, **kwargs):
        # Prefill parent_page in case the form is invalid (as prepopulated value for the form field,
        # because ModelChoiceField seems to not fall back to the user given value)
        self.parent_page = Page.objects.get(id=request.POST["new_parent_page"])
        return super().post(request, page_id, *args, **kwargs)

    def form_valid(self, form):
        # Receive the parent page (this should never be empty)
        if form.cleaned_data["new_parent_page"]:
            self.parent_page = form.cleaned_data["new_parent_page"]

        # Re-check if the user has permission to publish subpages on the new parent
        can_publish = self.parent_page.permissions_for_user(
            self.request.user
        ).can_publish_subpage()
        keep_live = can_publish and form.cleaned_data.get("publish_copies")

        # Copy the page
        if form.cleaned_data.get("alias"):
            action = CreatePageAliasAction(
                self.page.specific,
                recursive=form.cleaned_data.get("copy_subpages"),
                parent=self.parent_page,
                update_slug=form.cleaned_data["new_slug"],
                user=self.request.user,
            )
            new_page = action.execute(skip_permission_checks=True)
        else:
            action = CopyPageAction(
                page=self.page,
                recursive=form.cleaned_data.get("copy_subpages"),
                to=self.parent_page,
                update_attrs={
                    "title": form.cleaned_data["new_title"],
                    "slug": form.cleaned_data["new_slug"],
                },
                keep_live=keep_live,
                user=self.request.user,
            )
            new_page = action.execute()

        # Give a success message back to the user
        edit_button = messages.button(
            reverse("wagtailadmin_pages:edit", args=(new_page.id,)),
            _("Edit"),
        )
        if form.cleaned_data.get("copy_subpages"):
            messages.success(
                self.request,
                _("Page '%(page_title)s' and %(subpages_count)s subpages copied.")
                % {
                    "page_title": self.page.specific_deferred.get_admin_display_title(),
                    "subpages_count": new_page.get_descendants().count(),
                },
                buttons=[edit_button],
            )
        else:
            messages.success(
                self.request,
                _("Page '%(page_title)s' copied.")
                % {"page_title": self.page.specific_deferred.get_admin_display_title()},
                buttons=[edit_button],
            )

        for fn in hooks.get_hooks("after_copy_page"):
            result = fn(self.request, self.page, new_page)
            if hasattr(result, "status_code"):
                return result

        # Redirect to explore of parent page
        if self.next_url:
            return redirect(self.next_url)
        return redirect("wagtailadmin_explore", self.parent_page.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["next"] = self.next_url
        return context
