from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from wagtail import hooks
from wagtail.actions.delete_page import DeletePageAction
from wagtail.admin import messages
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.views.pages.utils import type_to_delete_confirmation
from wagtail.models import Page, ReferenceIndex


class DeleteView(TemplateView):
    template_name = "wagtailadmin/pages/confirm_delete.html"

    @method_decorator(transaction.atomic)
    def dispatch(self, request, page_id, *args, **kwargs):
        self.page = get_object_or_404(Page, id=page_id).specific
        if not self.page.permissions_for_user(request.user).can_delete():
            raise PermissionDenied

        self.wagtail_site_name = getattr(settings, "WAGTAIL_SITE_NAME", "wagtail")
        for fn in hooks.get_hooks("before_delete_page"):
            result = fn(request, self.page)
            if hasattr(result, "status_code"):
                return result

        self.next_url = get_valid_next_url_from_request(request)

        self.pages_to_delete = {self.page}

        # The `construct_translated_pages_to_cascade_actions` hook returns translation and
        # alias pages when the action is set to "delete"
        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            for fn in hooks.get_hooks("construct_translated_pages_to_cascade_actions"):
                fn_pages = fn([self.page], "delete")
                if fn_pages and isinstance(fn_pages, dict):
                    for additional_pages in fn_pages.values():
                        self.pages_to_delete.update(additional_pages)

        self.pages_to_delete = list(self.pages_to_delete)
        self.usage = ReferenceIndex.get_references_to(
            self.page
        ).group_by_source_object()
        return super().dispatch(request, page_id, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.usage.is_protected:
            raise PermissionDenied

        if not type_to_delete_confirmation(request):
            return self.render_to_response(self.get_context_data())

        parent_id = self.page.get_parent().id
        # Delete the source page.
        action = DeletePageAction(self.page, user=request.user)
        # Permission checks are done above, so skip them in execute.
        action.execute(skip_permission_checks=True)

        # Delete translation and alias pages if they have the same parent page.
        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            parent_page_translations = self.page.get_parent().get_translations()
            for page_or_alias in self.pages_to_delete:
                if page_or_alias.get_parent() in parent_page_translations:
                    action = DeletePageAction(page_or_alias, user=request.user)
                    # Permission checks are done above, so skip them in execute.
                    action.execute(skip_permission_checks=True)

        messages.success(
            request,
            _("Page '%(page_title)s' deleted.")
            % {"page_title": self.page.get_admin_display_title()},
        )

        for fn in hooks.get_hooks("after_delete_page"):
            result = fn(request, self.page)
            if hasattr(result, "status_code"):
                return result

        if self.next_url:
            return redirect(self.next_url)
        return redirect("wagtailadmin_explore", parent_id)

    def get_context_data(self, **kwargs):
        descendant_count = self.page.get_descendant_count()
        return {
            "page": self.page,
            "descendant_count": descendant_count,
            "next": self.next_url,
            "model_opts": self.page._meta,
            "usage_url": reverse("wagtailadmin_pages:usage", args=(self.page.id,))
            + "?describe_on_delete=1",
            "usage_count": self.usage.count(),
            "is_protected": self.usage.is_protected,
            # if the number of pages ( child pages + current page) exceeds this limit, then confirm before delete.
            "type_to_confirm_before_delete": (descendant_count + 1)
            >= getattr(settings, "WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT", 10),
            "wagtail_site_name": self.wagtail_site_name,
            # note that while pages_to_delete may contain a mix of translated pages
            # and aliases, we count the "translations" only, as aliases are similar
            # to symlinks, so they should just follow the source
            "translation_count": len(
                [
                    translation.id
                    for translation in self.pages_to_delete
                    if not translation.alias_of_id and translation.id != self.page.id
                ]
            ),
            "translation_descendant_count": sum(
                [
                    translation.get_descendants().filter(alias_of__isnull=True).count()
                    for translation in self.pages_to_delete
                ]
            ),
        }
