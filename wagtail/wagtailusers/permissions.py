from __future__ import absolute_import, unicode_literals

from wagtail.wagtailcore.permission_policies import ModelPermissionPolicy
from django.contrib.auth import get_user_model

User = get_user_model()

permission_policy = ModelPermissionPolicy(User)
