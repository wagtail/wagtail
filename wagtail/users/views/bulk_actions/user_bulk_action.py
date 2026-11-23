from django.contrib.auth import get_user_model

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin

User = get_user_model()


class UserBulkAction(PermissionCheckedMixin, BulkAction):
    models = [User]
    any_permission_required = ["add", "change", "delete"]
