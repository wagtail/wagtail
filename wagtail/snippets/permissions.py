from django.contrib.auth import get_permission_codename

from wagtail.snippets.models import get_snippet_models


def get_permission_name(action, model):
    return "{}.{}".format(
        model._meta.app_label,
        get_permission_codename(action, model._meta),
    )


def user_can_edit_snippet_type(user, model):
    """true if user has 'add', 'change' or 'delete' permission on this model"""
    for action in ("add", "change", "delete"):
        if user.has_perm(get_permission_name(action, model)):
            return True

    return False


def user_can_access_snippets(user, models=None):
    """
    true if user has 'add', 'change', 'delete', or 'view' permission
    on any model registered as a snippet type - or if a `models` list
    is passed, any of those models
    """
    if models is None:
        models = get_snippet_models()

    for model in models:
        if model.snippet_viewset.permission_policy.user_has_any_permission(
            user, {"add", "change", "delete", "view"}
        ):
            return True

    return False
