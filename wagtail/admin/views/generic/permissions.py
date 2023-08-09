from django.core.exceptions import PermissionDenied


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

    permission_policy = None
    permission_required = None
    any_permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_policy is not None:

            if self.permission_required is not None:
                if not self.user_has_permission(self.permission_required):
                    raise PermissionDenied

            if self.any_permission_required is not None:
                if not self.user_has_any_permission(self.any_permission_required):
                    raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission(self.request.user, permission)

    def user_has_any_permission(self, permissions):
        return self.permission_policy.user_has_any_permission(
            self.request.user, permissions
        )
