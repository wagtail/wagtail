from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.bulk_action.mixins import ReferenceIndexMixin
from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.admin.views.pages.utils import type_to_delete_confirmation


class DeleteBulkAction(ReferenceIndexMixin, PageBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = _("Delete selected pages")
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_delete.html"
    action_priority = 30
    classes = {"serious"}

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_delete()

    def object_context(self, page):
        return {
            **super().object_context(page),
            "descendant_count": page.get_descendant_count(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pages = context["items"]
        # Count the total number of pages including descendants
        total_page_count = len(pages) + sum(page["descendant_count"] for page in pages)
        wagtail_site_name = getattr(settings, "WAGTAIL_SITE_NAME", "wagtail")
        context.update(
            {
                "wagtail_site_name": wagtail_site_name,
                "total_page_count": total_page_count,
                # If the total page count exceeds this limit, then confirm before delete
                "type_to_confirm_before_delete": total_page_count
                >= getattr(settings, "WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT", 10),
            }
        )
        return context

    def post(self, request):
        if type_to_delete_confirmation(request):
            return super().post(request)
        else:
            # Re-render the confirmation page when site name verification fails
            return self.render_to_response(self.get_context_data())

    @classmethod
    def execute_action(cls, objects, user=None, **kwargs):
        num_parent_objects, num_child_objects = 0, 0
        for page in objects:
            num_parent_objects += 1
            num_child_objects += page.get_descendant_count()
            page.delete(user=user)
        return num_parent_objects, num_child_objects

    def get_usage_url(self, item):
        return (
            reverse("wagtailadmin_pages:usage", args=(item.pk,))
            + "?describe_on_delete=1"
        )

    def get_success_message(self, num_parent_objects, num_child_objects):
        if num_child_objects > 0:
            # Translators: This forms a message such as "1 page and 3 child pages have been deleted"
            return _("%(parent_pages)s and %(child_pages)s have been deleted") % {
                "parent_pages": self.get_parent_page_text(num_parent_objects),
                "child_pages": self.get_child_page_text(num_child_objects),
            }
        else:
            return ngettext(
                "%(num_parent_objects)d page has been deleted",
                "%(num_parent_objects)d pages have been deleted",
                num_parent_objects,
            ) % {"num_parent_objects": num_parent_objects}
