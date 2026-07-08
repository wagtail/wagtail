from wagtail.actions.edit import EditAction


class EditPageAction(EditAction):
    """
    Save changes to an existing page, creating a revision and logging a
    ``wagtail.edit`` action, the same as the admin's own edit view.

    See :class:`~wagtail.actions.edit.EditAction` for the parameters.
    """

    def user_has_permission(self):
        if not super().user_has_permission():
            return False
        return self.instance.permissions_for_user(self.user).can_edit()
