from django.db.models import Model

from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import BasePermissionPolicy, ModelPermissionPolicy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.utils.registry import ObjectTypeRegistry


class PolicyRegistry(ObjectTypeRegistry):
    """
    A registry that maps model classes to their permission policy instances.
    This is used by Wagtail to determine which permission policy to use for a
    given model class.

    Instead of using this class directly, use the global
    :obj:`~wagtail.permissions.policies_registry` instance and the
    :func:`~wagtail.permissions.register_permission_policy` function instead.
    """

    def get_by_type(self, cls: type[Model]) -> BasePermissionPolicy:
        """
        Get the permission policy for a given model class.
        If a matching policy was registered with ``exact_class=True``, it will be
        returned. Otherwise, the policy registered with ``exact_class=False`` for
        the given class or its nearest ancestor class will be returned. If no policy
        can be found, ``None`` will be returned.
        """
        return super().get_by_type(cls)

    def get(self, obj: Model) -> BasePermissionPolicy:
        """
        Get the permission policy for a given model instance based on its class.
        """
        return super().get(obj)


policies_registry = PolicyRegistry()
"""
A global instance of :class:`~wagtail.permissions.PolicyRegistry` used to
register and look up permission policies for models managed by Wagtail.
"""


def register_permission_policy(
    model: type[Model],
    policy: BasePermissionPolicy = None,
    exact_class=False,
):
    """
    Register a permission policy for a given model class.

    If no policy is provided, a default
    :class:`~wagtail.permission_policies.ModelPermissionPolicy` will be created.
    If ``exact_class`` is set to True, the policy will only be used for the
    exact model class, otherwise it will also be used for subclasses of the
    model class.
    """
    if policy is None:
        policy = ModelPermissionPolicy(model)
    policies_registry.register(model, value=policy, exact_class=exact_class)


page_permission_policy = PagePermissionPolicy(Page)
site_permission_policy = ModelPermissionPolicy(Site)
collection_permission_policy = CollectionManagementPermissionPolicy(Collection)
task_permission_policy = ModelPermissionPolicy(Task)
workflow_permission_policy = ModelPermissionPolicy(Workflow)
locale_permission_policy = ModelPermissionPolicy(Locale)

register_permission_policy(Page, page_permission_policy)
register_permission_policy(Site, site_permission_policy)
register_permission_policy(Collection, collection_permission_policy)
register_permission_policy(Task, task_permission_policy)
register_permission_policy(Workflow, workflow_permission_policy)
register_permission_policy(Locale, locale_permission_policy)
