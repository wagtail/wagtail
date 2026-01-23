from wagtail.contrib.redirects.models import Redirect
from wagtail.permission_policies import ModelPermissionPolicy

permission_policy = ModelPermissionPolicy(Redirect)
