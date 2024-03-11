import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.db.models.expressions import OuterRef, Subquery
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.models import (
    get_serializable_data_for_fields,
    model_from_serializable_data,
)

from wagtail.log_actions import log
from wagtail.utils.timestamps import ensure_utc

from .content_types import get_default_page_content_type
from .i18n import TranslatableMixin

logger = logging.getLogger("wagtail")


class RevisionQuerySet(models.QuerySet):
    def page_revisions_q(self):
        return Q(base_content_type=get_default_page_content_type())

    def page_revisions(self):
        return self.filter(self.page_revisions_q())

    def not_page_revisions(self):
        return self.exclude(self.page_revisions_q())

    def for_instance(self, instance):
        try:
            # Use RevisionMixin.get_base_content_type() if available
            return self.filter(
                base_content_type=instance.get_base_content_type(),
                object_id=str(instance.pk),
            )
        except AttributeError:
            # Fallback to ContentType for the model
            return self.filter(
                content_type=ContentType.objects.get_for_model(
                    instance, for_concrete_model=False
                ),
                object_id=str(instance.pk),
            )


class RevisionsManager(models.Manager.from_queryset(RevisionQuerySet)):
    def previous_revision_id_subquery(self, revision_fk_name="revision"):
        """
        Returns a Subquery that can be used to annotate a queryset with the ID
        of the previous revision, based on the revision_fk_name field. Useful
        to avoid N+1 queries when generating comparison links between revisions.

        The logic is similar to ``Revision.get_previous().pk``.
        """
        fk = revision_fk_name
        return Subquery(
            Revision.objects.filter(
                base_content_type_id=OuterRef(f"{fk}__base_content_type_id"),
                object_id=OuterRef(f"{fk}__object_id"),
            )
            .filter(
                Q(
                    created_at=OuterRef(f"{fk}__created_at"),
                    pk__lt=OuterRef(f"{fk}__pk"),
                )
                | Q(created_at__lt=OuterRef(f"{fk}__created_at"))
            )
            .order_by("-created_at", "-pk")
            .values_list("pk", flat=True)[:1]
        )


class PageRevisionsManager(RevisionsManager):
    def get_queryset(self):
        return RevisionQuerySet(self.model, using=self._db).page_revisions()


class Revision(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    base_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.CharField(
        max_length=255,
        verbose_name=_("object id"),
    )
    created_at = models.DateTimeField(db_index=True, verbose_name=_("created at"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wagtail_revisions",
    )
    object_str = models.TextField(default="")
    content = models.JSONField(
        verbose_name=_("content JSON"), encoder=DjangoJSONEncoder
    )
    approved_go_live_at = models.DateTimeField(
        verbose_name=_("approved go live at"), null=True, blank=True, db_index=True
    )

    objects = RevisionsManager()
    page_revisions = PageRevisionsManager()

    content_object = GenericForeignKey(
        "content_type", "object_id", for_concrete_model=False
    )

    wagtail_reference_index_ignore = True

    @cached_property
    def base_content_object(self):
        return self.base_content_type.get_object_for_this_type(pk=self.object_id)

    def save(self, user=None, *args, **kwargs):
        # Set default value for created_at to now
        # We cannot use auto_now_add as that will override
        # any value that is set before saving
        if self.created_at is None:
            self.created_at = timezone.now()

        # Set default value for base_content_type to the content_type.
        # Page revisions should set this to the default Page model's content type,
        # but the distinction may not be necessary for models that do not use inheritance.
        if self.base_content_type_id is None:
            self.base_content_type_id = self.content_type_id

        super().save(*args, **kwargs)

        if (
            self.approved_go_live_at is None
            and "update_fields" in kwargs
            and "approved_go_live_at" in kwargs["update_fields"]
        ):
            # Log scheduled revision publish cancellation
            object = self.as_object()
            # go_live_at = kwargs['update_fields'][]
            log(
                instance=object,
                action="wagtail.schedule.cancel",
                data={
                    "revision": {
                        "id": self.id,
                        "created": ensure_utc(self.created_at),
                        "go_live_at": ensure_utc(object.go_live_at)
                        if object.go_live_at
                        else None,
                        "has_live_version": object.live,
                    }
                },
                user=user,
                revision=self,
            )

    def as_object(self):
        return self.content_object.with_content_json(self.content)

    def is_latest_revision(self):
        if self.id is None:
            # special case: a revision without an ID is presumed to be newly-created and is thus
            # newer than any revision that might exist in the database
            return True

        latest_revision_id = (
            Revision.objects.filter(
                base_content_type_id=self.base_content_type_id,
                object_id=self.object_id,
            )
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
            .first()
        )
        return latest_revision_id == self.id

    def delete(self):
        # Update revision_created fields for comments that reference the current revision, if applicable.

        try:
            next_revision = self.get_next()
        except Revision.DoesNotExist:
            next_revision = None

        if next_revision:
            # move comments created on this revision to the next revision, as they may well still apply if they're unresolved
            self.created_comments.all().update(revision_created=next_revision)

        return super().delete()

    def publish(
        self,
        user=None,
        changed=True,
        log_action=True,
        previous_revision=None,
        skip_permission_checks=False,
    ):
        return self.content_object.publish(
            self,
            user=user,
            changed=changed,
            log_action=log_action,
            previous_revision=previous_revision,
            skip_permission_checks=skip_permission_checks,
        )

    def get_previous(self):
        return self.get_previous_by_created_at(
            base_content_type_id=self.base_content_type_id,
            object_id=self.object_id,
        )

    def get_next(self):
        return self.get_next_by_created_at(
            base_content_type_id=self.base_content_type_id,
            object_id=self.object_id,
        )

    def __str__(self):
        return '"' + str(self.content_object) + '" at ' + str(self.created_at)

    class Meta:
        verbose_name = _("revision")
        verbose_name_plural = _("revisions")
        indexes = [
            models.Index(
                fields=["content_type", "object_id"],
                name="content_object_idx",
            ),
            models.Index(
                fields=["base_content_type", "object_id"],
                name="base_content_object_idx",
            ),
        ]


class RevisionMixin(models.Model):
    """A mixin that allows a model to have revisions."""

    latest_revision = models.ForeignKey(
        "wagtailcore.Revision",
        related_name="+",
        verbose_name=_("latest revision"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
    )

    _revisions = GenericRelation(
        "wagtailcore.Revision",
        content_type_field="content_type",
        object_id_field="object_id",
        for_concrete_model=False,
    )
    """
    A default ``GenericRelation`` for the purpose of automatically deleting
    revisions when the object is deleted. This is not used to query the object's
    revisions. Instead, the :meth:`revisions` property is used for that purpose.
    As such, this default relation is considered private.

    This ``GenericRelation`` does not have a
    :attr:`~django.contrib.contenttypes.fields.GenericRelation.related_query_name`,
    so it cannot be used for reverse-related queries from ``Revision`` back to
    this model. If the feature is desired, subclasses can define their own
    ``GenericRelation`` to ``Revision`` with a custom ``related_query_name``.

    .. versionadded:: 7.1
        The default ``GenericRelation`` :attr:`~wagtail.models.RevisionMixin._revisions` was added.
    """

    # An array of additional field names that will not be included when the object is copied.
    default_exclude_fields_in_copy = [
        "latest_revision",
    ]

    @property
    def revisions(self):
        """
        Returns revisions that belong to the object. For non-page models, this
        is done by querying the :class:`~wagtail.models.Revision` model directly
        rather than using a
        :class:`~django.contrib.contenttypes.fields.GenericRelation`, to avoid
        `a known limitation <https://code.djangoproject.com/ticket/31269>`_ in
        Django for models with multi-table inheritance where the relation's
        content type may not match the instance's type.
        """
        return Revision.objects.for_instance(self)

    def get_base_content_type(self):
        parents = self._meta.get_parent_list()
        # Get the last non-abstract parent in the MRO as the base_content_type.
        # Note: for_concrete_model=False means that the model can be a proxy model.
        if parents:
            return ContentType.objects.get_for_model(
                parents[-1], for_concrete_model=False
            )
        # This model doesn't inherit from a non-abstract model,
        # use it as the base_content_type.
        return ContentType.objects.get_for_model(self, for_concrete_model=False)

    def get_content_type(self):
        return ContentType.objects.get_for_model(self, for_concrete_model=False)

    def get_latest_revision(self):
        return self.latest_revision

    def get_latest_revision_as_object(self):
        """
        Returns the latest revision of the object as an instance of the model.
        If no latest revision exists, returns the object itself.
        """
        latest_revision = self.get_latest_revision()
        if latest_revision:
            return latest_revision.as_object()
        return self

    def serializable_data(self):
        try:
            return super().serializable_data()
        except AttributeError:
            return get_serializable_data_for_fields(self)

    @classmethod
    def from_serializable_data(cls, data, check_fks=True, strict_fks=False):
        try:
            return super().from_serializable_data(data, check_fks, strict_fks)
        except AttributeError:
            return model_from_serializable_data(
                cls, data, check_fks=check_fks, strict_fks=strict_fks
            )

    def with_content_json(self, content):
        """
        Returns a new version of the object with field values updated to reflect changes
        in the provided ``content`` (which usually comes from a previously-saved revision).

        Certain field values are preserved in order to prevent errors if the returned
        object is saved, such as ``id``. The following field values are also preserved,
        as they are considered to be meaningful to the object as a whole, rather than
        to a specific revision:

        * ``latest_revision``

        If :class:`~wagtail.models.TranslatableMixin` is applied, the following field values
        are also preserved:

        * ``translation_key``
        * ``locale``
        """
        obj = self.from_serializable_data(content)

        # This should definitely never change between revisions
        obj.pk = self.pk

        # Ensure other values that are meaningful for the object as a whole
        # (rather than to a specific revision) are preserved
        obj.latest_revision = self.latest_revision

        if isinstance(self, TranslatableMixin):
            obj.translation_key = self.translation_key
            obj.locale = self.locale

        return obj

    def _update_from_revision(self, revision, changed=True):
        self.latest_revision = revision
        self.save(update_fields=["latest_revision"])

    def save_revision(
        self,
        user=None,
        approved_go_live_at=None,
        changed=True,
        log_action=False,
        previous_revision=None,
        clean=True,
    ):
        """
        Creates and saves a revision.

        :param user: The user performing the action.
        :param approved_go_live_at: The date and time the revision is approved to go live.
        :param changed: Indicates whether there were any content changes.
        :param log_action: Flag for logging the action. Pass ``True`` to also create a log entry. Can be passed an action string.
            Defaults to ``"wagtail.edit"`` when no ``previous_revision`` param is passed, otherwise ``"wagtail.revert"``.
        :param previous_revision: Indicates a revision reversal. Should be set to the previous revision instance.
        :type previous_revision: Revision
        :param clean: Set this to ``False`` to skip cleaning object content before saving this revision.
        :return: The newly created revision.
        """
        if clean:
            self.full_clean()

        revision = Revision.objects.create(
            content_object=self,
            base_content_type=self.get_base_content_type(),
            user=user,
            approved_go_live_at=approved_go_live_at,
            content=self.serializable_data(),
            object_str=str(self),
        )

        self._update_from_revision(revision, changed)

        logger.info(
            'Edited: "%s" pk=%d revision_id=%d', str(self), self.pk, revision.id
        )
        if log_action:
            if not previous_revision:
                log(
                    instance=self,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.edit",
                    user=user,
                    revision=revision,
                    content_changed=changed,
                )
            else:
                log(
                    instance=self,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.revert",
                    user=user,
                    data={
                        "revision": {
                            "id": previous_revision.id,
                            "created": ensure_utc(previous_revision.created_at),
                        }
                    },
                    revision=revision,
                    content_changed=changed,
                )

        return revision

    class Meta:
        abstract = True
