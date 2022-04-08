from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction


class DeleteBulkAction(PageBulkAction):
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
            "item": page,
            "descendant_count": page.get_descendant_count(),
        }

    @classmethod
    def execute_action(cls, objects, user=None, **kwargs):
        num_parent_objects, num_child_objects = 0, 0
        for page in objects:
            num_parent_objects += 1
            num_child_objects += page.get_descendant_count()
            page.delete(user=user)
        return num_parent_objects, num_child_objects

    def get_success_message(self, num_parent_objects, num_child_objects):
        if num_parent_objects == 1:
            if num_child_objects == 0:
                success_message = _("1 page has been deleted")
            else:
                success_message = ngettext(
                    "1 page and %(num_child_objects)d child page have been deleted",
                    "1 page and %(num_child_objects)d child pages have been deleted",
                    num_child_objects,
                ) % {"num_child_objects": num_child_objects}
        else:
            if num_child_objects == 0:
                success_message = _(
                    "%(num_parent_objects)d pages have been deleted"
                ) % {"num_parent_objects": num_parent_objects}
            else:
                success_message = ngettext(
                    "%(num_parent_objects)d pages and %(num_child_objects)d child page have been deleted",
                    "%(num_parent_objects)d pages and %(num_child_objects)d child pages have been deleted",
                    num_child_objects,
                ) % {
                    "num_child_objects": num_child_objects,
                    "num_parent_objects": num_parent_objects,
                }
        return success_message
