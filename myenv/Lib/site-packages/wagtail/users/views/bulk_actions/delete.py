from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.users.utils import user_can_delete_user
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction


class DeleteBulkAction(UserBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = _("Delete selected users")
    template_name = "wagtailusers/bulk_actions/confirm_bulk_delete.html"
    action_priority = 10
    classes = {"serious"}

    def check_perm(self, obj):
        return user_can_delete_user(self.request.user, obj)

    def get_execution_context(self):
        return {**super().get_execution_context(), "model": self.model}

    @classmethod
    def execute_action(cls, objects, model=None, **kwargs):
        if model is None:
            model = cls.get_default_model()
        model.objects.filter(pk__in=[obj.pk for obj in objects]).delete()
        return len(objects), 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return ngettext(
            "%(num_parent_objects)d user has been deleted",
            "%(num_parent_objects)d users have been deleted",
            num_parent_objects,
        ) % {"num_parent_objects": num_parent_objects}
