from wagtail.actions.edit import EditAction
from wagtail.permissions import page_permission_policy


class EditPageAction(EditAction):
    """
    Save changes to an existing page, creating a revision and logging a
    ``wagtail.edit`` action, the same as the admin's own edit view.

    See :class:`~wagtail.actions.edit.EditAction` for the parameters.
    """

    def __init__(self, instance, user=None, **kwargs):
        super().__init__(instance, user=user, **kwargs)
        # FIXME: use the registry
        self.permission_policy = page_permission_policy

    def user_has_permission(self):
        if not super().user_has_permission():
            return False
        return self.instance.permissions_for_user(self.user).can_edit()
