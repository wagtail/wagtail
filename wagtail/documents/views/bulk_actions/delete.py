from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction


class DeleteBulkAction(DocumentBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = _("Delete selected documents")
    template_name = "wagtaildocs/bulk_actions/confirm_bulk_delete.html"
    action_priority = 100
    classes = {"serious"}

    def check_perm(self, document):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, "delete", document
        )

    @classmethod
    def execute_action(cls, objects, **kwargs):
        num_parent_objects = len(objects)
        cls.get_default_model().objects.filter(
            pk__in=[obj.pk for obj in objects]
        ).delete()
        return num_parent_objects, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return ngettext(
            "%(num_parent_objects)d document has been deleted",
            "%(num_parent_objects)d documents have been deleted",
            num_parent_objects,
        ) % {"num_parent_objects": num_parent_objects}
