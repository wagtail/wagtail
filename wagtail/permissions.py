from django.conf import settings
from django.utils.module_loading import import_string

from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.base import BasePermissionPolicy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy, CollectionOwnershipPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy


def get_permission_policy(permission_policy_key: str, default: type[BasePermissionPolicy]) -> type[BasePermissionPolicy]:
    permission_policy_overrides: dict = getattr(settings, "WAGTAIL_PERMISSION_POLICY_OVERRIDES", {})
    permission_policy_import_string: str | None = permission_policy_overrides.get(permission_policy_key)

    if not permission_policy_import_string:
        return default
    
    overridden_permission_policy = import_string(permission_policy_import_string)

    if not issubclass(overridden_permission_policy, BasePermissionPolicy):
        raise ValueError(f"Overridden permission policy for '{permission_policy_key}' must be a subclass of BasePermissionPolicy")
    
    return overridden_permission_policy

model_permission_policy_class = get_permission_policy("model", default=ModelPermissionPolicy)
collection_ownership_permission_policy_class = get_permission_policy("collection_ownership", default=CollectionOwnershipPermissionPolicy)

page_permission_policy = get_permission_policy("page", default=PagePermissionPolicy)(Page)
collection_permission_policy = get_permission_policy("collection", default=CollectionManagementPermissionPolicy)(Collection)

site_permission_policy = get_permission_policy("site", default=model_permission_policy_class)(Site)
task_permission_policy = get_permission_policy("task", default=model_permission_policy_class)(Task)
workflow_permission_policy = get_permission_policy("workflow", default=model_permission_policy_class)(Workflow)
locale_permission_policy = get_permission_policy("locale", default=model_permission_policy_class)(Locale)
