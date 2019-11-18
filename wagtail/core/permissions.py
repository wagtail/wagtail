from wagtail.core.models import Collection, Site, Task, Workflow
from wagtail.core.permission_policies import ModelPermissionPolicy

site_permission_policy = ModelPermissionPolicy(Site)
collection_permission_policy = ModelPermissionPolicy(Collection)
task_permission_policy = ModelPermissionPolicy(Task)
workflow_permission_policy = ModelPermissionPolicy(Workflow)
