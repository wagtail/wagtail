from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.core import hooks


class DeleteBulkAction(PageBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = "Delete pages"
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_delete.html"
    action_priority = 30
    classes = {'serious'}

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_delete()

    def object_context(self, page):
        return {
            'page': page,
            'descendant_count': page.get_descendant_count(),
        }

    def execute_action(self, pages):
        for page in pages:
            self.num_parent_objects += 1
            self.num_child_objects += page.get_descendant_count()
            page.delete(user=self.request.user)

    def get_success_message(self):
        if self.num_parent_objects == 1:
            if self.num_child_objects == 0:
                success_message = _("1 page has been deleted")
            else:
                success_message = ngettext(
                    "1 page and %(num_child_objects)d child page have been deleted",
                    "1 page and %(num_child_objects)d child pages have been deleted",
                    self.num_child_objects
                ) % {
                    'num_child_objects': self.num_child_objects
                }
        else:
            if self.num_child_objects == 0:
                success_message = _("%(num_parent_objects)d pages have been deleted") % {'num_parent_objects': self.num_parent_objects}
            else:
                success_message = ngettext(
                    "%(num_parent_objects)d pages and %(num_child_objects)d child page have been deleted",
                    "%(num_parent_objects)d pages and %(num_child_objects)d child pages have been deleted",
                    self.num_child_objects
                ) % {
                    'num_child_objects': self.num_child_objects,
                    'num_parent_objects': self.num_parent_objects
                }
        return success_message


@hooks.register('register_page_bulk_action')
def delete(request):
    return DeleteBulkAction(request)
