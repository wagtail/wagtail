from __future__ import absolute_import, unicode_literals

from wagtail.wagtailcore.permission_policies import ModelPermissionPolicy
from wagtail.wagtailredirects.models import Redirect

permission_policy = ModelPermissionPolicy(Redirect)
