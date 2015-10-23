def user_can_edit_setting_type(user, model):
    """ Check if a user has permission to edit this setting type """
    return user.has_perm("{}.change_{}".format(
        model._meta.app_label, model._meta.model_name))
