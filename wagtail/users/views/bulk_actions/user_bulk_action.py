from django.contrib.auth import get_user_model

from wagtail.admin.views.bulk_action import BulkAction


class UserBulkAction(BulkAction):
    models = [get_user_model()]
    object_key = 'user'
