import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from wagtail.log_actions import log
from wagtail.signals import page_published

logger = logging.getLogger("wagtail")


class PublishPagePermissionError(PermissionDenied):
    """
    Raised when the page publish cannot be performed due to insufficient permissions.
    """

    pass


class PublishPageRevisionAction:
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

    def __init__(
        self, revision, user=None, changed=True, log_action=True, previous_revision=None
    ):
        self.revision = revision
        self.page = self.revision.as_page_object()
        self.user = user
        self.changed = changed
        self.log_action = log_action
        self.previous_revision = previous_revision

    def check(self, skip_permission_checks=False):
        if (
            self.user
            and not skip_permission_checks
            and not self.page.permissions_for_user(self.user).can_publish()
        ):
            raise PublishPagePermissionError(
                "You do not have permission to publish this page"
            )

    def log_scheduling_action(self):
        log(
            instance=self.page,
            action="wagtail.publish.schedule",
            user=self.user,
            data={
                "revision": {
                    "id": self.revision.id,
                    "created": self.revision.created_at.strftime("%d %b %Y %H:%M"),
                    "go_live_at": self.page.go_live_at.strftime("%d %b %Y %H:%M"),
                    "has_live_version": self.page.live,
                }
            },
            revision=self.revision,
            content_changed=self.changed,
        )

    def _publish_page_revision(
        self, revision, page, user, changed, log_action, previous_revision
    ):
        from wagtail.models import COMMENTS_RELATION_NAME, PageRevision

        if page.go_live_at and page.go_live_at > timezone.now():
            page.has_unpublished_changes = True
            # Instead set the approved_go_live_at of this revision
            revision.approved_go_live_at = page.go_live_at
            revision.save()
            # And clear the the approved_go_live_at of any other revisions
            page.revisions.exclude(id=revision.id).update(approved_go_live_at=None)
            # if we are updating a currently live page skip the rest
            if page.live_revision:
                # Log scheduled publishing
                if log_action:
                    self.log_scheduling_action()

                return
            # if we have a go_live in the future don't make the page live
            page.live = False
        else:
            page.live = True
            # at this point, the page has unpublished changes if and only if there are newer revisions than this one
            page.has_unpublished_changes = not revision.is_latest_revision()
            # If page goes live clear the approved_go_live_at of all revisions
            page.revisions.update(approved_go_live_at=None)
        page.expired = False  # When a page is published it can't be expired

        # Set first_published_at, last_published_at and live_revision
        # if the page is being published now
        if page.live:
            now = timezone.now()
            page.last_published_at = now
            page.live_revision = revision

            if page.first_published_at is None:
                page.first_published_at = now

            if previous_revision:
                previous_revision_page = previous_revision.as_page_object()
                old_page_title = (
                    previous_revision_page.title
                    if page.title != previous_revision_page.title
                    else None
                )
            else:
                try:
                    previous = revision.get_previous()
                except PageRevision.DoesNotExist:
                    previous = None
                old_page_title = (
                    previous.page.title
                    if previous and page.title != previous.page.title
                    else None
                )
        else:
            # Unset live_revision if the page is going live in the future
            page.live_revision = None

        page.save()

        for comment in getattr(page, COMMENTS_RELATION_NAME).all().only("position"):
            comment.save(update_fields=["position"])

        revision.submitted_for_moderation = False
        page.revisions.update(submitted_for_moderation=False)

        workflow_state = page.current_workflow_state
        if workflow_state and getattr(
            settings, "WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH", True
        ):
            workflow_state.cancel(user=user)

        if page.live:
            page_published.send(
                sender=page.specific_class, instance=page.specific, revision=revision
            )

            # Update alias pages
            page.update_aliases(revision=revision, user=user, _content=revision.content)

            if log_action:
                data = None
                if previous_revision:
                    data = {
                        "revision": {
                            "id": previous_revision.id,
                            "created": previous_revision.created_at.strftime(
                                "%d %b %Y %H:%M"
                            ),
                        }
                    }

                if old_page_title:
                    data = data or {}
                    data["title"] = {
                        "old": old_page_title,
                        "new": page.title,
                    }

                    log(
                        instance=page,
                        action="wagtail.rename",
                        user=user,
                        data=data,
                        revision=revision,
                    )

                log(
                    instance=page,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.publish",
                    user=user,
                    data=data,
                    revision=revision,
                    content_changed=changed,
                )

            logger.info(
                'Page published: "%s" id=%d revision_id=%d',
                page.title,
                page.id,
                revision.id,
            )
        elif page.go_live_at:
            logger.info(
                'Page scheduled for publish: "%s" id=%d revision_id=%d go_live_at=%s',
                page.title,
                page.id,
                revision.id,
                page.go_live_at.isoformat(),
            )

            if log_action:
                self.log_scheduling_action()

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        return self._publish_page_revision(
            self.revision,
            self.page,
            user=self.user,
            changed=self.changed,
            log_action=self.log_action,
            previous_revision=self.previous_revision,
        )
