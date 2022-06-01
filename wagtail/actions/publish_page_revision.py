import logging

from django.conf import settings

from wagtail.actions.publish_revision import (
    PublishPermissionError,
    PublishRevisionAction,
)
from wagtail.signals import page_published

logger = logging.getLogger("wagtail")


class PublishPagePermissionError(PublishPermissionError):
    """
    Raised when the page publish cannot be performed due to insufficient permissions.
    """

    pass


class PublishPageRevisionAction(PublishRevisionAction):
    """
    Publish or schedule revision for publishing.

    :param revision: revision to publish
    :param user: the publishing user
    :param changed: indicated whether content has changed
    :param log_action:
        flag for the logging action. Pass False to skip logging. Cannot pass an action string as the method
        performs several actions: "publish", "revert" (and publish the reverted revision),
        "schedule publishing with a live revision", "schedule revision reversal publishing, with a live revision",
        "schedule publishing", "schedule revision reversal publishing"
    :param previous_revision: indicates a revision reversal. Should be set to the previous revision instance
    """

    def check(self, skip_permission_checks=False):
        if (
            self.user
            and not skip_permission_checks
            and not self.object.permissions_for_user(self.user).can_publish()
        ):
            raise PublishPagePermissionError(
                "You do not have permission to publish this page"
            )

    def _after_publish(self):
        from wagtail.models import COMMENTS_RELATION_NAME

        for comment in (
            getattr(self.object, COMMENTS_RELATION_NAME).all().only("position")
        ):
            comment.save(update_fields=["position"])

        page_published.send(
            sender=self.object.specific_class,
            instance=self.object.specific,
            revision=self.revision,
        )

        super()._after_publish()

        workflow_state = self.object.current_workflow_state
        if workflow_state and getattr(
            settings, "WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH", True
        ):
            workflow_state.cancel(user=self.user)

        self.object.update_aliases(
            revision=self.revision, user=self.user, _content=self.revision.content
        )
