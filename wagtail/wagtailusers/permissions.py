from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model

from wagtail.wagtailcore.permission_policies import ModelPermissionPolicy


User = get_user_model()

permission_policy = ModelPermissionPolicy(User)
