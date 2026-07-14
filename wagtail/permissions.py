from django.core.exceptions import ImproperlyConfigured
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
    :obj:`~wagtail.permissions.policy_registry` instance and the
    :func:`~wagtail.permissions.register_permission_policy` function instead.
    """

    fallback_policies = {}
    """
    A dict that stores fallback permission policies for models that have not
    registered a custom permission policy. Having this as a separate dict
    allows us to ensure custom permission policies are registered before any
    code attempts to retrieve them from the registry.
    """

    def get_fallback_policy(self, cls: type[Model]) -> BasePermissionPolicy | None:
        """
        Get the fallback permission policy for a given model class,
        if a fallback was registered.
        """
        return self.fallback_policies.get(cls)

    def get_by_type(self, cls: type[Model], fallback=True) -> BasePermissionPolicy:
        """
        Get the permission policy for a given model class.
        If a matching policy was registered with ``exact_class=True``, it will be
        returned. Otherwise, the policy registered with ``exact_class=False`` for
        the given class or its nearest ancestor class will be returned. If no policy
        can be found and ``fallback`` is True, a default fallback
        :class:`~wagtail.permission_policies.ModelPermissionPolicy` will be used.
        Otherwise, return ``None``.
        """
        if not (policy := super().get_by_type(cls)):
            if fallback and not (policy := self.get_fallback_policy(cls)):
                self.fallback_policies[cls] = policy = ModelPermissionPolicy(cls)
        return policy

    def get(self, obj: Model) -> BasePermissionPolicy:
        """
        Get the permission policy for a given model instance based on its class.
        """
        return super().get(obj)

    def register(self, cls, value=None, exact_class=False):
        if self.get_fallback_policy(cls):
            raise ImproperlyConfigured(
                f"A fallback permission policy has already been created for "
                f"{cls._meta.label}. Please ensure your custom "
                f"{value.__class__.__name__} is registered earlier on, such as "
                f"at the top of wagtail_hooks.py or in your AppConfig.ready()."
            )
        return super().register(cls, value, exact_class)


policy_registry = PolicyRegistry()
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
    policy_registry.register(model, value=policy, exact_class=exact_class)


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
