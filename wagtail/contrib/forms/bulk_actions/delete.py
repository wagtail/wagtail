from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.contrib.forms.bulk_actions.form_bulk_action import FormSubmissionBulkAction


class DeleteBulkAction(FormSubmissionBulkAction):
    display_name = _("Delete")
    aria_label = _("Delete selected objects")
    action_type = "delete"
    template_name = "bulk_actions/confirm_bulk_delete.html"

    @classmethod
    def execute_action(cls, objects, **kwargs):
        num_forms = 0
        print(objects)
        for obj in objects:
            num_forms = num_forms + 1
            obj.delete()
        return num_forms, 0

    def get_success_message(self, count, num_child_objects):

        return ngettext(
            "One submission has been deleted.",
            "%(count)d submissions have been deleted.",
            count,
        ) % {"count": count}