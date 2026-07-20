from wagtail.actions.create import CreateAction
from wagtail.permissions import page_permission_policy


class CreatePageAction(CreateAction):
    """
    Save a new page to the database under ``parent``, creating a revision and
    logging the same ``wagtail.create`` + ``wagtail.edit`` pair of log entries
    the admin's own create view produces.

    :param instance: the (unsaved) page to create.
    :param parent: the page to create ``instance`` under.

    See :class:`~wagtail.actions.create.CreateAction` for the remaining
    parameters.
    """

    def __init__(self, instance, parent, user=None, **kwargs):
        # Page.save() called via .add_child() always logs its own
        # "wagtail.create". Instead of using the CreateAction's default
        # "wagtail.create" log_action here, use "wagtail.edit" instead.
        # This also matches the admin create view that logs a "wagtail.edit"
        # entry (via save_revision(log_action=True)) after creation.
        super().__init__(instance, user=user, log_action="wagtail.edit", **kwargs)
        self.parent = parent
        # FIXME: use the registry
        self.permission_policy = page_permission_policy

    def user_has_permission(self):
        if not super().user_has_permission():
            return False
        if not self.parent.permissions_for_user(self.user).can_add_subpage():
            return False
        model = type(self.instance)
        if (
            model not in self.parent.creatable_subpage_models()
            or not model.can_create_at(self.parent)
        ):
            return False
        return True

    def _save_instance(self):
        from wagtail.models import PageSubscription

        self.instance.live = False
        self.parent.add_child(instance=self.instance)
        # TODO: Set page privacy setting, needs duplicating/extracting logic
        # from the admin views, so do this later.

        if self.user:
            PageSubscription.objects.update_or_create(
                page=self.instance,
                user=self.user,
                defaults={"comment_notifications": True},
            )

        if self.form:
            # Might not be necessary, as the admin create view doesn't do this.
            self.form.save_m2m()
