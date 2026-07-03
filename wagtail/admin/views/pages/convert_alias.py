from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from wagtail import hooks
from wagtail.actions.convert_alias import ConvertAliasPageAction
from wagtail.admin import messages
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.models import Page


class ConvertAliasView(TemplateView):
    template_name = "wagtailadmin/pages/confirm_convert_alias.html"

    @method_decorator(transaction.atomic)
    def dispatch(self, request, page_id, *args, **kwargs):
        self.page = get_object_or_404(
            Page, id=page_id, alias_of_id__isnull=False
        ).specific
        if not self.page.permissions_for_user(request.user).can_edit():
            raise PermissionDenied

        for fn in hooks.get_hooks("before_convert_alias_page"):
            result = fn(request, self.page)
            if hasattr(result, "status_code"):
                return result

        self.next_url = get_valid_next_url_from_request(request)
        return super().dispatch(request, page_id, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = ConvertAliasPageAction(self.page, user=request.user)
        action.execute(skip_permission_checks=True)

        messages.success(
            request,
            _("Page '%(page_title)s' has been converted into an ordinary page.")
            % {"page_title": self.page.get_admin_display_title()},
        )

        for fn in hooks.get_hooks("after_convert_alias_page"):
            result = fn(request, self.page)
            if hasattr(result, "status_code"):
                return result

        if self.next_url:
            return redirect(self.next_url)
        return redirect("wagtailadmin_pages:edit", self.page.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["next_url"] = self.next_url
        return context
