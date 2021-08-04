from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.users.utils import user_can_delete_user
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction


class DeleteBulkAction(UserBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = _("Delete users")
    template_name = "wagtailusers/bulk_actions/confirm_bulk_delete.html"
    action_priority = 10
    classes = {'serious'}

    def check_perm(self, obj):
        return user_can_delete_user(self.request.user, obj)

    @classmethod
    def execute_action(cls, objects, **kwargs):
        cls.model.objects.filter(pk__in=[obj.pk for obj in objects]).delete()
        cls.num_parent_objects = len(objects)

    def get_success_message(self):
        return ngettext(
            "%(num_parent_objects)d user has been deleted",
            "%(num_parent_objects)d users have been deleted",
            self.num_parent_objects
        ) % {
            'num_parent_objects': self.num_parent_objects
        }


@hooks.register('register_user_bulk_action')
def delete(request):
    return DeleteBulkAction(request)
