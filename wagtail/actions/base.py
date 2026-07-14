from django.core.exceptions import PermissionDenied
from django.utils.functional import cached_property


class BaseAction:
    """
    Base class for actions.

    An action encapsulates a single mutation of a model instance (creating,
    editing, deleting, publishing, and so on) along with its permission checks,
    audit logging, and signals. This keeps the business logic in one place so
    that admin views, the API, and code calling into Wagtail programmatically
    all behave identically.

    Subclasses set the :attr:`action_name` and :attr:`permission_policy_action`
    attributes and implement :meth:`execute`.
    """

    action_name: str | None = None
    """
    The name the action is registered under in the action registry, e.g.
    ``"create"``. Used by :class:`~wagtail.actions.registry.ActionRegistry`.
    """

    permission_policy_action: str | None = None
    """
    The action string passed to the permission policy, e.g. ``"add"``,
    ``"change"`` or ``"delete"``.
    """

    permission_error_class = PermissionDenied
    """
    The :class:`~django.core.exceptions.PermissionDenied` subclass raised by
    ``check()`` when the permission check fails.
    """

    def __init__(self, instance, user=None):
        self.instance = instance
        self.user = user

    @cached_property
    def permission_policy(self):
        """
        The permission policy used to check permissions for the instance.

        By default, it is retrieved from the permission policy registry, before
        falling back to a plain
        ``wagtail.permission_policies.ModelPermissionPolicy`` for models
        that have not registered one.
        """
        from wagtail.permissions import policy_registry

        return policy_registry.get(self.instance)

    def user_has_permission(self):
        """
        Return whether ``self.user`` is allowed to perform the action.

        The default implementation checks ``permission_policy_action`` against
        the instance. Subclasses may override this to perform a model-level
        check (for actions such as "create" where there is no existing
        instance to check against) or to combine multiple checks.
        """
        return self.permission_policy.user_has_permission_for_instance(
            self.user, self.permission_policy_action, self.instance
        )

    def check(self, skip_permission_checks=False):
        """
        Raise a :class:`~django.core.exceptions.PermissionDenied` subclass if
        the user is not allowed to perform the action. This is a no-op when no
        user is given or ``skip_permission_checks`` is ``True``.
        """
        if self.user and not skip_permission_checks and not self.user_has_permission():
            raise self.permission_error_class(
                f"You do not have permission to perform the "
                f"'{self.action_name}' action on this object."
            )

    def execute(self, skip_permission_checks=False):
        """
        Run :meth:`check` and then perform the action, returning the affected
        instance.
        """
        raise NotImplementedError
