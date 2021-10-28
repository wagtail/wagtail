from wagtail.models import Collection, Locale, Site, workflows
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.collections import CollectionMangementPermissionPolicy


site_permission_policy = ModelPermissionPolicy(Site)
collection_permission_policy = CollectionMangementPermissionPolicy(Collection)
task_permission_policy = ModelPermissionPolicy(workflows.Task)
workflow_permission_policy = ModelPermissionPolicy(workflows.Workflow)
locale_permission_policy = ModelPermissionPolicy(Locale)
