from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.search import SearchArea
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.permission_policies import ModelPermissionPolicy
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


# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = f"{AUTH_USER_APP_LABEL}.add_{AUTH_USER_MODEL_NAME.lower()}"
change_user_perm = "{}.change_{}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
delete_user_perm = "{}.delete_{}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)


class UsersSearchArea(SearchArea):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register("register_admin_search_area")
def register_users_search_area():
    return UsersSearchArea(
        _("Users"),
        reverse("wagtailusers_users:index"),
        name="users",
        icon_name="user",
        order=600,
    )


User = get_user_model()


class UserAdminURLFinder(ModelAdminURLFinder):
    edit_url_name = "wagtailusers_users:edit"
    permission_policy = ModelPermissionPolicy(User)


register_admin_url_finder(User, UserAdminURLFinder)


for action_class in [AssignRoleBulkAction, DeleteBulkAction, SetActiveStateBulkAction]:
    hooks.register("register_bulk_action", action_class)
