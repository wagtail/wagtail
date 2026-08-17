from wagtail.actions.edit import EditAction, EditPermissionError


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

    def check_publish(self):
        if (
            self.user
            and self.publish
            and not self.instance.permissions_for_user(self.user).can_publish()
        ):
            raise EditPermissionError(
                "You do not have permission to publish this page."
            )
