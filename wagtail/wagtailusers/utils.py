from __future__ import absolute_import, unicode_literals


def user_can_delete_user(context, user, user_has_delete_user_perm):
    context_user = context.user
    can_delete = user_has_delete_user_perm and user.pk != context_user.pk
    if not context_user.is_superuser:
        can_delete = can_delete and not user.is_superuser
    return can_delete
