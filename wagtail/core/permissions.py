from wagtail.core.models import Collection, Site, Workflow
from wagtail.core.permission_policies import ModelPermissionPolicy

site_permission_policy = ModelPermissionPolicy(Site)
collection_permission_policy = ModelPermissionPolicy(Collection)
workflow_permission_policy = ModelPermissionPolicy(Workflow)
