from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy

from django.conf import settings
from django.utils.module_loading import import_string

def override_permission_policy(policy: str, default):
    """
    Override permission policy from settings
    """
    permission_policy_overrides = getattr(settings, "WAGTAIL_PERMISSION_POLICY_OVERRIDES", {})
    permission_policy = permission_policy_overrides.get(policy)
    if permission_policy:
        return import_string(permission_policy)
    return default
     

page_permission_policy = override_permission_policy("page", PagePermissionPolicy(Page))
site_permission_policy = override_permission_policy("site", ModelPermissionPolicy(Site))
collection_permission_policy = override_permission_policy("collection", CollectionManagementPermissionPolicy(Collection))
task_permission_policy = override_permission_policy("task", ModelPermissionPolicy(Task))
workflow_permission_policy = override_permission_policy("workflow", ModelPermissionPolicy(Workflow))
locale_permission_policy = override_permission_policy("locale", ModelPermissionPolicy(Locale))
