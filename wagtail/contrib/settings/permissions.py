from django.contrib.contenttypes.models import ContentType


def user_can_edit_setting_type(user, model):
    """ Check if a user has any permission related to a content type """
    if not user.is_active:
        return False

    if user.is_superuser:
        return True

    content_type = ContentType.objects.get_for_model(model)
    permission_codenames = content_type.permission_set.values_list('codename', flat=True)
    for codename in permission_codenames:
        permission_name = "%s.%s" % (content_type.app_label, codename)
        if user.has_perm(permission_name):
            return True

    return False
