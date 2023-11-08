import logging

from wagtail.actions.unpublish import UnpublishAction, UnpublishPermissionError
from wagtail.signals import page_unpublished

logger = logging.getLogger("wagtail")


class UnpublishPagePermissionError(UnpublishPermissionError):
    """
    Raised when the page unpublish cannot be performed due to insufficient permissions.
    """

    pass


class UnpublishPageAction(UnpublishAction):
    def __init__(
        self,
        page,
        set_expired=False,
        commit=True,
        user=None,
        log_action=True,
        include_descendants=False,
    ):
        super().__init__(
            page,
            set_expired=set_expired,
            commit=commit,
            user=user,
            log_action=log_action,
        )
        self.include_descendants = include_descendants

    def check(self, skip_permission_checks=False):
        try:
            super().check(skip_permission_checks)
        except UnpublishPermissionError as error:
            raise UnpublishPagePermissionError(
                "You do not have permission to unpublish this page"
            ) from error

    def _commit_unpublish(self, object):
        # using clean=False to bypass validation
        object.save(clean=False)

    def _after_unpublish(self, object):
        for alias in object.aliases.all():
            alias.unpublish(log_action=False)

        page_unpublished.send(sender=object.specific_class, instance=object.specific)

        super()._after_unpublish(object)

    def execute(self, skip_permission_checks=False):
        super().execute(skip_permission_checks)

        if self.include_descendants:

            for live_descendant_page in (
                self.object.get_descendants()
                .live()
                .defer_streamfields()
                .specific()
                .iterator()
            ):
                action = UnpublishPageAction(live_descendant_page)
                if live_descendant_page.permissions_for_user(self.user).can_unpublish():
                    action.execute(skip_permission_checks=True)
