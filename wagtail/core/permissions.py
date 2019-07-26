from wagtail.core.models import Collection, get_site_model
from wagtail.core.permission_policies import ModelPermissionPolicy


def get_site_permission_policy():
    Site = get_site_model()
    return ModelPermissionPolicy(Site)


collection_permission_policy = ModelPermissionPolicy(Collection)
