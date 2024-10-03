from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from wagtail import hooks
from wagtail.users.views.bulk_actions import (
    AssignRoleBulkAction,
    DeleteBulkAction,
    SetActiveStateBulkAction,
)


def get_viewset_cls(app_config, viewset_name):
    try:
        viewset_cls = import_string(getattr(app_config, viewset_name))
    except (AttributeError, ImportError) as e:
        raise ImproperlyConfigured(
            f"Invalid setting for {app_config.__class__.__name__}.{viewset_name}: {e}"
        )
    return viewset_cls


@hooks.register("register_admin_viewset")
def register_viewset():
    app_config = apps.get_app_config("wagtailusers")
    user_viewset_cls = get_viewset_cls(app_config, "user_viewset")
    group_viewset_cls = get_viewset_cls(app_config, "group_viewset")
    return [
        user_viewset_cls("wagtailusers_users", url_prefix="users"),
        group_viewset_cls("wagtailusers_groups", url_prefix="groups"),
    ]


for action_class in [AssignRoleBulkAction, DeleteBulkAction, SetActiveStateBulkAction]:
    hooks.register("register_bulk_action", action_class)
