import logging

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
        try:
            super().check(skip_permission_checks)
        except PublishPermissionError as error:
            raise PublishPagePermissionError(
                "You do not have permission to publish this page"
            ) from error

    def _send_published_signal(self, object, revision):
        page_published.send(
            sender=object.specific_class,
            instance=object.specific,
            revision=revision,
        )
