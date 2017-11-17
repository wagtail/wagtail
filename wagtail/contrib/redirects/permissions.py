from __future__ import absolute_import, unicode_literals

from wagtail.core.permission_policies import ModelPermissionPolicy
from wagtail.contrib.redirects.models import Redirect

permission_policy = ModelPermissionPolicy(Redirect)
