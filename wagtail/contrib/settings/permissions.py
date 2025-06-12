from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.sites import SitePermissionPolicy


def get_permission_policy(model):
    """
    Get the permission policy for a given model.
    If the model is a BaseSiteSetting, return SitePermissionPolicy.
    Otherwise, return ModelPermissionPolicy.
    """
    from .models import BaseSiteSetting

    if issubclass(model, BaseSiteSetting):
        return SitePermissionPolicy(model)
    else:
        return ModelPermissionPolicy(model)


def user_can_edit_setting_type(user, model):
    """Check if a user has permission to edit this setting type"""
    return user.has_perm(f"{model._meta.app_label}.change_{model._meta.model_name}")
