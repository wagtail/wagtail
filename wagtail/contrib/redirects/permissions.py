from wagtail.contrib.redirects.models import Redirect
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permissions import override_permission_policy


permission_policy = override_permission_policy("redirect", ModelPermissionPolicy(Redirect))
