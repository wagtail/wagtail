from wagtail.core.models import Collection, get_site_model
from wagtail.core.permission_policies import ModelPermissionPolicy

Site = get_site_model()
site_permission_policy = ModelPermissionPolicy(Site)


collection_permission_policy = ModelPermissionPolicy(Collection)
