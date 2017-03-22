from __future__ import absolute_import, unicode_literals

from wagtail.wagtailcore.models import Site
from wagtail.wagtailcore.permission_policies import ModelPermissionPolicy

site_permission_policy = ModelPermissionPolicy(Site)
