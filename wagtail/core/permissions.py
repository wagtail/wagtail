from wagtail.core.models import Collection, Locale, Site, Task, Workflow
from wagtail.core.permission_policies import ModelPermissionPolicy
from wagtail.core.permission_policies.collections import CollectionMangementPermissionPolicy


site_permission_policy = ModelPermissionPolicy(Site)
collection_permission_policy = CollectionMangementPermissionPolicy(Collection)
task_permission_policy = ModelPermissionPolicy(Task)
workflow_permission_policy = ModelPermissionPolicy(Workflow)
locale_permission_policy = ModelPermissionPolicy(Locale)
