from wagtail.wagtailcore.permission_policies import ModelPermissionPolicy
from wagtail.wagtailredirects.models import Redirect


permission_policy = ModelPermissionPolicy(Redirect)
