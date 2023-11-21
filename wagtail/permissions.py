from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.base import BasePermissionPolicy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.utils.registry import ObjectTypeRegistry

policies_registry = ObjectTypeRegistry[BasePermissionPolicy]()


def register_permission_policy(model, policy):
    policies_registry.register(model, value=policy)


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
