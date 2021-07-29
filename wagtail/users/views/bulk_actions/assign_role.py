from django import forms
from django.contrib.auth.models import Group
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.core.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction


change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


class RoleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'] = forms.ModelChoiceField(
            queryset=Group.objects.all()
        )


class AssignRoleBulkAction(UserBulkAction):
    display_name = _("Assign role")
    action_type = "assign_role"
    aria_label = _("Assign role to users")
    template_name = "wagtailusers/bulk_actions/confirm_bulk_assign_role.html"
    action_priority = 30
    form_class = RoleForm

    def check_perm(self, obj):
        return self.request.user.has_perm(change_user_perm)

    def get_execution_context(self):
        return {
            'role': self.cleaned_form.cleaned_data['role'],
            'user': self.request.user
        }

    def prepare_action(self, objects):
        if not self.request.user.is_superuser:
            return
        for user in objects:
            if user == self.request.user:
                ctx = self.get_context_data()
                ctx['users'] = list(filter(lambda x: x['user'].pk != user.pk, ctx['users']))
                ctx['mark_self_as_not_admin'] = [user]
                return TemplateResponse(self.request, self.template_name, ctx)

    @classmethod
    def execute_action(cls, objects, **kwargs):
        cls.role = role = kwargs.get('role', None)
        if role is None:
            return
        for user in objects:
            user.groups.add(role)
            user.save()
            cls.num_parent_objects += 1

    def get_success_message(self):
        return ngettext(
            "%(num_parent_objects)d user has been assigned as %(role)s",
            "%(num_parent_objects)d users have been assigned as %(role)s",
            self.num_parent_objects
        ) % {
            'num_parent_objects': self.num_parent_objects,
            'role': self.role
        }


@hooks.register('register_user_bulk_action')
def assign_role(request):
    return AssignRoleBulkAction(request)
