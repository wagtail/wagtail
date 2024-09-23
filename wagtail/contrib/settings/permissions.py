def user_can_edit_setting_type(user, model):
    """Check if a user has permission to edit this setting type"""
    return user.has_perm(f"{model._meta.app_label}.change_{model._meta.model_name}")
