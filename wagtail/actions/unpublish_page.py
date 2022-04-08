import logging

from django.core.exceptions import PermissionDenied

from wagtail.log_actions import log
from wagtail.signals import page_unpublished

logger = logging.getLogger("wagtail")


class UnpublishPagePermissionError(PermissionDenied):
    """
    Raised when the page unpublish cannot be performed due to insufficient permissions.
    """

    pass


class UnpublishPageAction:
    def __init__(
        self,
        page,
        set_expired=False,
        commit=True,
        user=None,
        log_action=True,
        include_descendants=False,
    ):
        self.page = page
        self.set_expired = set_expired
        self.commit = commit
        self.user = user
        self.log_action = log_action
        self.include_descendants = include_descendants

    def check(self, skip_permission_checks=False):
        if (
            self.user
            and not skip_permission_checks
            and not self.page.permissions_for_user(self.user).can_unpublish()
        ):
            raise UnpublishPagePermissionError(
                "You do not have permission to unpublish this page"
            )

    def _unpublish_page(self, page, set_expired, commit, user, log_action):
        """
        Unpublish the page by setting ``live`` to ``False``. Does nothing if ``live`` is already ``False``
        :param log_action: flag for logging the action. Pass False to skip logging. Can be passed an action string.
            Defaults to 'wagtail.unpublish'
        """
        if page.live:
            page.live = False
            page.has_unpublished_changes = True
            page.live_revision = None

            if set_expired:
                page.expired = True

            if commit:
                # using clean=False to bypass validation
                page.save(clean=False)

            page_unpublished.send(sender=page.specific_class, instance=page.specific)

            if log_action:
                log(
                    instance=page,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.unpublish",
                    user=user,
                )

            logger.info('Page unpublished: "%s" id=%d', page.title, page.id)

            page.revisions.update(approved_go_live_at=None)

            # Unpublish aliases
            for alias in page.aliases.all():
                alias.unpublish()

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        self._unpublish_page(
            self.page,
            set_expired=self.set_expired,
            commit=self.commit,
            user=self.user,
            log_action=self.log_action,
        )

        if self.include_descendants:
            from wagtail.models import UserPagePermissionsProxy

            user_perms = UserPagePermissionsProxy(self.user)
            for live_descendant_page in (
                self.page.get_descendants().live().defer_streamfields().specific()
            ):
                action = UnpublishPageAction(live_descendant_page)
                if user_perms.for_page(live_descendant_page).can_unpublish():
                    action.execute(skip_permission_checks=True)
