from django.core.exceptions import PermissionDenied
from django.utils.functional import cached_property

from wagtail.permissions import policy_registry


class PermissionCheckedMixin:
    """
    Mixin for class-based views to enforce permission checks according to
    a permission policy (see wagtail.permission_policies).

    To take advantage of this, subclasses should set the class property:
    * permission_policy (a policy object)
    and either of:
    * permission_required (an action name such as 'add', 'change' or 'delete')
    * any_permission_required (a list of action names - the user must have
      one or more of those permissions)
    """

    permission_required = None
    any_permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_required is not None:
            if not self.user_has_permission(self.permission_required):
                raise PermissionDenied

        if self.any_permission_required is not None:
            if not self.user_has_any_permission(self.any_permission_required):
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def permission_policy(self):
        return getattr(self, "model", None) and policy_registry.get_by_type(self.model)

    def user_has_permission(self, permission):
        return not self.permission_policy or (
            self.permission_policy.user_has_permission(self.request.user, permission)
        )

    def user_has_permission_for_instance(self, permission, instance):
        return not self.permission_policy or (
            self.permission_policy.user_has_permission_for_instance(
                self.request.user, permission, instance
            )
        )

    def user_has_any_permission(self, permissions):
        return not self.permission_policy or (
            self.permission_policy.user_has_any_permission(
                self.request.user, permissions
            )
        )
