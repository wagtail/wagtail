from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction
from wagtail.users.views.users import change_user_perm


class RoleForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Group.objects.all())


class AssignRoleBulkAction(UserBulkAction):
    display_name = _("Assign role")
    action_type = "assign_role"
    aria_label = _("Assign role to selected users")
    template_name = "wagtailusers/bulk_actions/confirm_bulk_assign_role.html"
    action_priority = 30
    form_class = RoleForm

    def check_perm(self, obj):
        return self.request.user.has_perm(change_user_perm)

    def get_execution_context(self):
        return {
            "role": self.cleaned_form.cleaned_data["role"],
        }

    @classmethod
    def execute_action(cls, objects, role=None, **kwargs):
        if role is None:
            return
        role.user_set.add(*objects)
        num_parent_objects = len(objects)
        return num_parent_objects, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return ngettext(
            "%(num_parent_objects)d user has been assigned as %(role)s",
            "%(num_parent_objects)d users have been assigned as %(role)s",
            num_parent_objects,
        ) % {
            "num_parent_objects": num_parent_objects,
            "role": self.cleaned_form.cleaned_data["role"].name,
        }
