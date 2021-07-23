from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction


class DeleteBulkAction(DocumentBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = _("Delete documents")
    template_name = "wagtaildocs/bulk_actions/confirm_bulk_delete.html"
    action_priority = 10
    classes = {'serious'}

    def check_perm(self, document):
        return self.permission_policy.user_has_permission_for_instance(self.request.user, 'delete', document)

    @classmethod
    def execute_action(cls, objects, **kwargs):
        for document in objects:
            cls.num_parent_objects += 1
            document.delete()

    def get_success_message(self):
        return ngettext(
            "%(num_parent_objects)d document has been deleted",
            "%(num_parent_objects)d documents have been deleted",
            self.num_parent_objects
        ) % {
            'num_parent_objects': self.num_parent_objects
        }


@hooks.register('register_document_bulk_action')
def delete(request):
    return DeleteBulkAction(request)
