from wagtail.contrib.forms.bulk_actions.form_bulk_action import FormBulkAction
from django.utils.translation import gettext_lazy as _


class DeleteBulkAction(FormBulkAction):
    display_name = _("Delete")
    aria_label = _("Delete selected objects")
    action_type = "delete"
    template_name = "wagtailforms/bulk_actions/confirm_bulk_delete.html"

    @classmethod
    def execute_action(cls, objects, **kwargs):
        num_forms = 0
        for obj in objects:
            num_forms = num_forms + 1
            obj.delete()
        return num_forms, cls.action_type
