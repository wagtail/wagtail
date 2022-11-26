from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.actions.unpublish_page import UnpublishPageAction
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.views.generic.models import UnpublishView
from wagtail.models import Page, UserPagePermissionsProxy


class Unpublish(UnpublishView):
    model = Page
    index_url_name = "wagtailadmin_explore"
    edit_url_name = "wagtailadmin_pages:edit"
    unpublish_url_name = "wagtailadmin_pages:unpublish"
    success_message = _("Page '%(page_title)s' unpublished.")
    template_name = "wagtailadmin/pages/confirm_unpublish.html"

    def setup(self, request, page_id, *args, **kwargs):
        # Rename path kwargs from pk to page_id
        return super().setup(request, page_id, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Page, id=self.pk).specific

    def get_object_display_title(self):
        return self.object.get_admin_display_title()

    def dispatch(self, request, *args, **kwargs):
        user_perms = UserPagePermissionsProxy(request.user)
        if not user_perms.for_page(self.object).can_unpublish():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_message(self):
        return self.success_message % {
            "page_title": self.object.get_admin_display_title()
        }

    def get_next_url(self):
        next_url = get_valid_next_url_from_request(self.request)
        if next_url:
            return next_url
        return reverse(self.index_url_name, args=(self.object.get_parent().id,))

    def get_objects_to_unpublish(self):
        objects_to_unpublish = {self.object}

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            for fn in hooks.get_hooks("construct_translated_pages_to_cascade_actions"):
                fn_pages = fn([self.object], "unpublish")
                if fn_pages and isinstance(fn_pages, dict):
                    for additional_pages in fn_pages.values():
                        objects_to_unpublish.update(additional_pages)

        return list(objects_to_unpublish)

    def unpublish(self):
        hook_response = self.run_hook(
            "before_unpublish_page", self.request, self.object
        )
        if hook_response is not None:
            return hook_response

        include_descendants = self.request.POST.get("include_descendants", False)

        for object in self.objects_to_unpublish:
            action = UnpublishPageAction(
                object, user=self.request.user, include_descendants=include_descendants
            )
            action.execute(skip_permission_checks=True)

        hook_response = self.run_hook("after_unpublish_page", self.request, self.object)
        if hook_response is not None:
            return hook_response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page": self.object,
                "live_descendant_count": self.object.get_descendants().live().count(),
                "translation_count": len(self.objects_to_unpublish[1:]),
                "translation_descendant_count": sum(
                    [
                        p.get_descendants().filter(alias_of__isnull=True).live().count()
                        for p in self.objects_to_unpublish[1:]
                    ]
                ),
            }
        )
        return context
