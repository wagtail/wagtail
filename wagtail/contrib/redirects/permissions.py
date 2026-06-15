from wagtail.contrib.redirects.models import Redirect
from wagtail.permissions import get_permission_policy, model_permission_policy_class


permission_policy = get_permission_policy("redirect", default=model_permission_policy_class)(Redirect)
