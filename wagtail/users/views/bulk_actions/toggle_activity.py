from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction
from wagtail.users.views.users import change_user_perm


class ActivityForm(forms.Form):
    mark_as_active = forms.BooleanField(
        required=False,
        label=_('Activate / Deactivate')
    )


class ToggleActivityBulkAction(UserBulkAction):
    display_name = _("Toggle activity")
    action_type = "toggle_activity"
    aria_label = _("Mark users as active or inactive")
    template_name = "wagtailusers/bulk_actions/confirm_bulk_toggle_activity.html"
    action_priority = 20
    form_class = ActivityForm

    def check_perm(self, obj):
        return self.request.user.has_perm(change_user_perm)

    def get_execution_context(self):
        return {
            'mark_as_active': self.cleaned_form.cleaned_data['mark_as_active'],
            'user': self.request.user
        }

    def get_actionable_objects(self):
        objects, objects_without_access = super().get_actionable_objects()
        user = self.request.user
        users = list(filter(lambda x: x.pk != user.pk, objects))
        if len(objects) != len(users):
            objects_without_access['mark_self_as_inactive'] = [user]
        return users, objects_without_access

    @classmethod
    def execute_action(cls, objects, mark_as_active=False, user=None, **kwargs):
        if user is not None:
            objects = list(filter(lambda x: x.pk != user.pk, objects))
        num_parent_objects = cls.model.objects.filter(pk__in=[obj.pk for obj in objects]).update(is_active=mark_as_active)
        return num_parent_objects, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        if self.cleaned_form.cleaned_data['mark_as_active']:
            return ngettext(
                "%(num_parent_objects)d user has been marked as active",
                "%(num_parent_objects)d users have been marked as active",
                num_parent_objects
            ) % {
                'num_parent_objects': num_parent_objects,
            }
        else:
            return ngettext(
                "%(num_parent_objects)d user has been marked as inactive",
                "%(num_parent_objects)d users have been marked as inactive",
                num_parent_objects
            ) % {
                'num_parent_objects': num_parent_objects,
            }


@hooks.register('register_user_bulk_action')
def toggle_activity(request):
    return ToggleActivityBulkAction(request)
