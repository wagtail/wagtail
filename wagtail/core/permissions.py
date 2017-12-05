from wagtail.core.models import Site
from wagtail.core.permission_policies import ModelPermissionPolicy

site_permission_policy = ModelPermissionPolicy(Site)
