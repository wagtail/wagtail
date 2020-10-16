from wagtail.contrib.redirects.models import Redirect
from wagtail.core.permission_policies import ModelPermissionPolicy


permission_policy = ModelPermissionPolicy(Redirect)
