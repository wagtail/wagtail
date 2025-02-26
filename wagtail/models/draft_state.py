from django.core import checks
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.actions.publish_revision import PublishRevisionAction
from wagtail.actions.unpublish import UnpublishAction
from wagtail.locks import ScheduledForPublishLock

from .revisions import RevisionMixin


class DraftStateMixin(models.Model):
    live = models.BooleanField(verbose_name=_("live"), default=True, editable=False)
    has_unpublished_changes = models.BooleanField(
        verbose_name=_("has unpublished changes"), default=False, editable=False
    )

    first_published_at = models.DateTimeField(
        verbose_name=_("first published at"), blank=True, null=True, db_index=True
    )
    last_published_at = models.DateTimeField(
        verbose_name=_("last published at"), null=True, editable=False
    )
    live_revision = models.ForeignKey(
        "wagtailcore.Revision",
        related_name="+",
        verbose_name=_("live revision"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
    )

    go_live_at = models.DateTimeField(
        verbose_name=_("go live date/time"), blank=True, null=True
    )
    expire_at = models.DateTimeField(
        verbose_name=_("expiry date/time"), blank=True, null=True
    )
    expired = models.BooleanField(
        verbose_name=_("expired"), default=False, editable=False
    )

    class Meta:
        abstract = True

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_revision_mixin(),
        ]

    @classmethod
    def _check_revision_mixin(cls):
        mro = cls.mro()
        error = checks.Error(
            "DraftStateMixin requires RevisionMixin to be applied after DraftStateMixin.",
            hint="Add RevisionMixin to the model's base classes after DraftStateMixin.",
            obj=cls,
            id="wagtailcore.E004",
        )

        try:
            if mro.index(RevisionMixin) < mro.index(DraftStateMixin):
                return [error]
        except ValueError:
            return [error]

        return []

    @property
    def approved_schedule(self):
        return self.scheduled_revision is not None

    @property
    def status_string(self):
        if not self.live:
            if self.expired:
                return _("expired")
            elif self.approved_schedule:
                return _("scheduled")
            else:
                return _("draft")
        else:
            if self.approved_schedule:
                return _("live + scheduled")
            elif self.has_unpublished_changes:
                return _("live + draft")
            else:
                return _("live")

    def publish(
        self,
        revision,
        user=None,
        changed=True,
        log_action=True,
        previous_revision=None,
        skip_permission_checks=False,
    ):
        """
        Publish a revision of the object by applying the changes in the revision to the live object.

        :param revision: Revision to publish.
        :type revision: Revision
        :param user: The publishing user.
        :param changed: Indicated whether content has changed.
        :param log_action: Flag for the logging action, pass ``False`` to skip logging.
        :param previous_revision: Indicates a revision reversal. Should be set to the previous revision instance.
        :type previous_revision: Revision
        """
        return PublishRevisionAction(
            revision,
            user=user,
            changed=changed,
            log_action=log_action,
            previous_revision=previous_revision,
        ).execute(skip_permission_checks=skip_permission_checks)

    def unpublish(self, set_expired=False, commit=True, user=None, log_action=True):
        """
        Unpublish the live object.

        :param set_expired: Mark the object as expired.
        :param commit: Commit the changes to the database.
        :param user: The unpublishing user.
        :param log_action: Flag for the logging action, pass ``False`` to skip logging.
        """
        return UnpublishAction(
            self,
            set_expired=set_expired,
            commit=commit,
            user=user,
            log_action=log_action,
        ).execute()

    def with_content_json(self, content):
        """
        Similar to :meth:`RevisionMixin.with_content_json`,
        but with the following fields also preserved:

        * ``live``
        * ``has_unpublished_changes``
        * ``first_published_at``
        """
        obj = super().with_content_json(content)

        # Ensure other values that are meaningful for the object as a whole (rather than
        # to a specific revision) are preserved
        obj.live = self.live
        obj.has_unpublished_changes = self.has_unpublished_changes
        obj.first_published_at = self.first_published_at

        return obj

    def get_latest_revision_as_object(self):
        if not self.has_unpublished_changes:
            # Use the live database copy in preference to the revision record, as:
            # 1) this will pick up any changes that have been made directly to the model,
            #    such as automated data imports;
            # 2) it ensures that inline child objects pick up real database IDs even if
            #    those are absent from the revision data. (If this wasn't the case, the child
            #    objects would be recreated with new IDs on next publish - see #1853)
            return self

        latest_revision = self.get_latest_revision()

        if latest_revision:
            return latest_revision.as_object()
        else:
            return self

    @cached_property
    def scheduled_revision(self):
        return self.revisions.filter(approved_go_live_at__isnull=False).first()

    def get_scheduled_revision_as_object(self):
        scheduled_revision = self.scheduled_revision
        return scheduled_revision and scheduled_revision.as_object()

    def _update_from_revision(self, revision, changed=True):
        update_fields = ["latest_revision"]
        self.latest_revision = revision

        if changed:
            self.has_unpublished_changes = True
            update_fields.append("has_unpublished_changes")

        self.save(update_fields=update_fields)

    def get_lock(self):
        # Scheduled publishing lock should take precedence over other locks
        if self.approved_schedule:
            return ScheduledForPublishLock(self)
        return super().get_lock()
