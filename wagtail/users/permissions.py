from wagtail.permissions import get_permission_policy, model_permission_policy_class
from django.contrib.auth import get_user_model

User = get_user_model()

permission_policy = get_permission_policy("user", default=model_permission_policy_class)(User)