from wagtail.core.permission_policies import ModelPermissionPolicy
from wagtail.contrib.redirects.models import Redirect

permission_policy = ModelPermissionPolicy(Redirect)
